# AWS Audit Scripts

You should install awscli and jq before using these. These will accept input
from STDIN, making them amenable to receiving piped input.

| Script        | Purpose       |
| ------------- |:-------------:|
| iam_inline_policies_in_use.sh | Find IAM inline policies in use. |
| iam_accounts_not_used.sh | Find IAM users who have never logged in on the console or used the API. |
| minimum_password_length.sh | Print the minimum password length set by the account's password policy. |
| rds_instance_unencrypted_storage.sh | Find RDS instances using unencrypted storage. |
| s3_buckets_logging_disabled.sh | Find S3 buckets with access logging disabled. |
| s3_buckets_world_writeable.sh | Find S3 buckets allowing world (everyone) write access. |
| s3_buckets_world_readable.sh | Find S3 buckets allowing world (everyone) read access. |
