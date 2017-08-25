#!/bin/bash
# Accepts newline delimited AWS profiles from STDIN (piped input works well).
PROFILES=$(cat -)

# For each given profile, find if any of the S3 buckets don't have access logging.
# Outputs in the following format:
# <profile> <s3 bucket>
for PROFILE in $PROFILES; do
    for BUCKET in $(aws --profile ${PROFILE} s3api list-buckets | jq -r '.Buckets[].Name'); do
        LOGGING_POLICY=$(aws --profile ${PROFILE} s3api get-bucket-logging --bucket ${BUCKET})
    
        if [ -z "${LOGGING_POLICY}" ]; then
            echo "$PROFILE $BUCKET"
        fi
    done
done
