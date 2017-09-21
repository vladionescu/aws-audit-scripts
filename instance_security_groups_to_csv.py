#!/usr/bin/env python
import argparse, subprocess, sys
import json, csv

parser = argparse.ArgumentParser(description='Show which instances have which SGs in a CSV format.')
parser.add_argument('-p', '--profile', required=True,
        help='the awscli profile to use')
parser.add_argument('-r', '--region', required=False, default="us-west-2",
        help='the region to scan (default: us-west-2)')
parser.add_argument('-o', '--output', required=False, default="instance_sgs.csv",
        help='csv output filename (default: instance_sgs.csv)')

args = parser.parse_args()

"""
Get a JSON string of instances and their SGs, looks like:
[
    {
      "Instance": "bastion",
      "SGs": [
	"sg-allow-ssh",
      ]
    },
    {
      "Instance": "web1",
      "SGs": [
	"sg-allow-http",
	"sg-allow-mysql"
      ]
    }
]
"""
command = "aws --profile " + args.profile + " --region " + args.region + " ec2 describe-instances | jq '[.Reservations[].Instances[] | {Instance: (.Tags[]|select(.Key==\"Name\")|.Value), SGs: [(.SecurityGroups[]|.GroupName)]}]'"

aws_out = subprocess.check_output(command, shell=True)
objects = json.loads(aws_out)

# Get a sorted unique list of all SG names -- pythonic magic
sg_names = sorted(list(set(x for l in [x['SGs'] for x in objects] for x in l)))

"""
CSV output format:

Instance,sg-allow-http,sg-allow-ssh,sg-allow-mysql
bastion,,X,
web1,X,,X
web2,X,,X
db1,,,X
db2,,,X
"""
# Write the header row which will include every SG name
file_out = csv.writer(open(args.output, "wb+"))
file_out.writerow(['Instance'] + sg_names)

# Write the instance row which will include the instance name and an X in every
# column where it has that SG
for instance in objects:
    index_of_attached_sgs = [sg_names.index(sg) for sg in instance['SGs']]
    sg_list = []

    for i in xrange(len(sg_names)):
        if i in index_of_attached_sgs:
            sg_list.append('X')
        else:
            sg_list.append('')

    file_out.writerow([instance['Instance']] + sg_list )
