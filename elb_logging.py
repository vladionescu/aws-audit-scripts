#!/usr/bin/env python
import argparse, json, subprocess, sys

def main():
    parser = argparse.ArgumentParser(description=('Manage ELBv2/ALB logging '
            'state. First displays all ELBv2 names and whether logging is '
            'enabled or not. If logging is enabled, it also displays the S3 '
            'bucket (and optional prefix) configured. Next, if an S3 bucket name '
            'is specified, the script can enable logging on all ELBv2 resources '
            'via the --enable-all flag, or if that flag is not set it will '
            'prompt interactively to enable logging on a per-ELB basis. If the '
            'destination S3 bucket does not exist, it will be created. The '
            'destination S3 bucket will receive a policy enabling the official '
            'ELB accounts to PUT objects in it - this policy is applied with '
            'prejudice and any existing policy will be overwritten.'))
    parser.add_argument('-p', '--profile', required=True,
            help='the awscli profile to use')
    parser.add_argument('-r', '--region', required=False, default="us-west-2",
            help='the region to scan (default: us-west-2)')
    parser.add_argument('-n', '--dry-run', required=False, action='store_true', default=False,
            help="print the ELB logging state and any state changing commands that would have been executed")
    parser.add_argument('-y', '--enable-all', required=False, action='store_true', default=False,
            help="enable logging on all ELBs")
    parser.add_argument('-b', '--bucket', required=False,
            help="destination bucket for logs, required to enable logging")
    parser.add_argument('-d', '--prefix', required=False,
            help="prefix for destination bucket for logs")

    args = parser.parse_args()

    """
    Get all the ELBv2 Names and ARNs in this account in this region
    """
    command = "aws --profile " + args.profile + " --region " + args.region + \
            " elbv2 describe-load-balancers | jq '[.LoadBalancers[] | {arn: .LoadBalancerArn, name: .LoadBalancerName}]'"

    aws_out = subprocess.check_output(command, shell=True)
    elbs = json.loads(aws_out)

    """
    Get logging status of each ELB
    """
    for elb in elbs:
        command = "aws --profile " + args.profile + " --region " + args.region + \
                " elbv2 describe-load-balancer-attributes --load-balancer-arn " + \
                elb['arn'] + " | jq '[.Attributes[] | select( .Key  | contains(\"access_logs\") )]'"

        aws_out = subprocess.check_output(command, shell=True)
        json_object = json.loads(aws_out)
        print_elb_name_and_log_state(elb, json_object)

    """
    Check that we can enable logging on ELBs
    """
    if args.bucket is None:
        print "[Warning] You didn't specify an S3 bucket, so I can't enable logging."
        sys.exit(1)

    if args.dry_run:
        print "These would have been executed next (dry run):"

    create_s3_bucket(args)

    """
    Enable logging on existing ELBs
    """
    for elb in elbs:
        """
        Ask to enable logging (interactive mode) iff --enable-all is not specified
        """
        if not args.enable_all:
            if not query_yes_no("Enable logging for " + elb['name'] + "?", "no"):
                continue

        prefix = ""
        if args.prefix is not None:
            prefix = "Key=access_logs.s3.prefix,Value={prefix}".format(prefix=args.prefix)

        print "Enabling logging on " + elb['name']
        command = "aws --profile " + args.profile + " --region " + args.region + \
                " elbv2 modify-load-balancer-attributes --load-balancer-arn " + elb['arn'] + \
                " --attributes Key=access_logs.s3.enabled,Value=true" + \
                " Key=access_logs.s3.bucket,Value=" + args.bucket + " " + prefix + \
                " | jq '[.Attributes[] | select( .Key  | contains(\"access_logs\") )]'"

        if args.dry_run:
            print "# " + command
        else:
            try:
                aws_out = subprocess.check_output(command, shell=True)
            except subprocess.CalledProcessError as e:
                # The awscli will output errors to stderr, no need to throw
                # a traceback as well
                continue

            json_object = json.loads(aws_out)
            print_elb_name_and_log_state(elb, json_object)

"""
Print ELB names and their logging status
"""
def print_elb_name_and_log_state(elb, json_attributes):
    elb_attributes = {item['Key']: item['Value'] for item in json_attributes}

    log_destination = ""
    if elb_attributes['access_logs.s3.enabled'] == "true":
        log_destination = " -> s3://{bucket}/{prefix}".format(
            bucket=elb_attributes['access_logs.s3.bucket'],
            prefix=elb_attributes['access_logs.s3.prefix'])

    print("{name} (Logging: {state}{log_destination})".format(name=elb['name'],
        state=elb_attributes['access_logs.s3.enabled'], log_destination=log_destination))

"""
Try to create the destination S3 bucket
If the bucket exists this will fail and that's ok
We are attempting to create it instead of checking if it exists
Because the bucket may be owned by another account and our ELBs
May have write access to it while we may not have read access
"""
def create_s3_bucket(args):
    print "Attempting to create bucket " + args.bucket + " in " + args.region
    print "(This will fail if it already exists, and that's okay)"
    command = "aws --profile " + args.profile + " --region " + args.region + \
            " s3api create-bucket --bucket " + args.bucket + \
            " --create-bucket-configuration LocationConstraint=" + args.region

    if args.dry_run:
        print "# " + command
    else:
        try:
            aws_out = subprocess.check_output(command, shell=True)
        except subprocess.CalledProcessError as e:
            # The awscli will output errors to stderr, no need to throw a
            # traceback as well
            pass

    """
    Set the bucket policy to allow writes from AWS' ELBs in this region
    """
    region_to_elb_account = {
        "us-east-1": "127311923021",
        "us-east-2": "033677994240",
        "us-west-1": "027434742980",
        "us-west-2": "797873946194",
        "ca-central-1": "985666609251",
        "eu-west-1": "156460612806",
        "eu-central-1": "054676820928",
        "eu-west-2": "652711504416",
        "ap-northeast-1": "582318560864",
        "ap-northeast-2": "600734575887",
        "ap-southeast-1": "114774131450",
        "ap-southeast-2": "783225319266",
        "ap-south-1": "718504428378",
        "sa-east-1": "507241528517",
    }
    elb_account = region_to_elb_account[args.region]

    prefix = ""
    if args.prefix is not None:
        prefix = "/" + args.prefix

    command = "aws --profile " + args.profile + " --region " + args.region + \
            " sts get-caller-identity | jq -j '.Account'"
    account_number = subprocess.check_output(command, shell=True)

    policy = """{{
  "Id": "Policy1508194878619",
  "Version": "2012-10-17",
  "Statement": [
    {{
      "Sid": "Stmt1508194872005",
      "Action": [
        "s3:PutObject"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:s3:::{bucket}{prefix}/AWSLogs/{account_number}/*",
      "Principal": {{
        "AWS": [
          "{elb_account}"
        ]
      }}
    }}
  ]
}}""".format(bucket=args.bucket, prefix=prefix, account_number=account_number,
        elb_account=elb_account)

    print "Setting the policy on " + args.bucket
    command = "aws --profile " + args.profile + " --region " + args.region + \
            " s3api put-bucket-policy --bucket " + args.bucket + \
            " --policy '" + policy + "'"

    if args.dry_run:
        print "# " + command
    else:
        try:
            aws_out = subprocess.check_output(command, shell=True)
        except subprocess.CalledProcessError as e:
            # The awscli will output errors to stderr, no need to throw a
            # traceback as well
            pass

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

if __name__ == "__main__":
    main()
