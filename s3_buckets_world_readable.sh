#!/bin/bash
# Accepts newline delimited AWS profiles from STDIN (piped input works well).
PROFILES=$(cat -)

# For each given profile, find if any of the S3 buckets allow everyone (anonymous users or any authenticated AWS users) the following permissions:
#   READ or FULL_ACCESS (read/write/modify permissions)
# Outputs in the following format:
# <profile> <s3 bucket> <permissions>
for PROFILE in $PROFILES; do
    for BUCKET in $(aws --profile ${PROFILE} s3api list-buckets | jq -r '.Buckets[].Name'); do
        ACLS=$(aws --profile ${PROFILE} s3api get-bucket-acl --bucket ${BUCKET} | \
            jq -r '.Grants[] | select(.Grantee.URI == "http://acs.amazonaws.com/groups/global/AllUsers" or .Grantee.URI == "http://acs.amazonaws.com/groups/global/AuthenticatedUsers").Permission')
    
        if [ ! -z "${ACLS}" ]; then
            if [[ "${ACLS}" == *"READ"* ]] || [[ "${ACLS}" == *"FULL"* ]]; then
                echo $ACLS | xargs echo "$PROFILE $BUCKET"
            fi
        fi
    done
done
