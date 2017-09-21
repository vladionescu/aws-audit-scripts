# AWS Audit Scripts

You should install awscli and jq before using these. Bash scripts accept input
from STDIN, making them amenable to receiving piped input. Python scripts take
command line arguments.

| Script        | Purpose       |
| ------------- |:-------------:|
| iam_inline_policies_in_use.sh | Find IAM inline policies in use. |
| iam_accounts_not_used.sh | Find IAM users who have never logged in on the console or used the API. |
| minimum_password_length.sh | Print the minimum password length set by the account's password policy. |
| rds_instance_unencrypted_storage.sh | Find RDS instances using unencrypted storage. |
| s3_buckets_logging_disabled.sh | Find S3 buckets with access logging disabled. |
| s3_buckets_world_writeable.sh | Find S3 buckets allowing world (everyone) write access. |
| s3_buckets_world_readable.sh | Find S3 buckets allowing world (everyone) read access. |
| instance_security_groups_to_csv.py | Get a CSV matrix of instances and their SGs. |

## Example Usage

Bash scripts accept a newline delimited list of profiles to run against via
STDIN. Profiles are the same ones stored in ~/.aws/credentials and
~/.aws/config.

```bash
$ ls
list_of_profiles    s3_buckets_logging_disabled.sh
$ cat list_of_profiles
project1-dev
project1-prod
project2-test
personal-site
$ cat list_of_profiles | ./s3_buckets_logging_disabled.sh | tee s3_buckets_logging_disabled.out
project2-test my-bucket
personal-site personal-site-bucket-1
$ ls
list_of_profiles    s3_buckets_logging_disabled.sh  s3_buckets_logging_disabled.out
```

Python scripts use argparse and have their own functionality, use `-h` for
details.
