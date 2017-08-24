#!/bin/bash
# Accepts newline delimited AWS profiles from STDIN (piped input works well).
PROFILES=$(cat -)

# For each given profile, find if any of the RDS instances use unencrypted storage.
# Outputs in the following format:
# <profile> <region> <RDS instance ID>
for PROFILE in $PROFILES; do
    for REGION in $(aws --profile ${PROFILE} --region us-west-2 ec2 describe-regions | jq -r '.Regions[].RegionName'); do
        INSTANCES=$(aws --profile ${PROFILE} --region ${REGION} rds describe-db-instances | jq -r '.DBInstances[] | select(.StorageEncrypted == false).DBInstanceIdentifier')
    
        if [ ! -z "${INSTANCES}" ]; then
            for INSTANCE in $INSTANCES; do
                echo "$PROFILE $REGION $INSTANCE"
            done
        fi
    done # REGION
done # PROFILE
