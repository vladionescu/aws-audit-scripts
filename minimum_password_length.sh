#!/bin/bash
# Accepts newline delimited AWS profiles from STDIN (piped input works well).
PROFILES=$(cat -)

# For each given profile, print the minimum password length as set by the password policy.
# Outputs in the following format:
# <profile> <min length>
for PROFILE in $PROFILES; do
    LENGTH=$(aws --profile ${PROFILE} iam get-account-password-policy | jq -r '.PasswordPolicy.MinimumPasswordLength')

    if [ ! -z "${LENGTH}" ]; then
        echo "$PROFILE $LENGTH"
    fi
done
