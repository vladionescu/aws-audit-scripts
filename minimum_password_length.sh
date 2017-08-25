#!/bin/bash
# Accepts newline delimited AWS profiles from STDIN (piped input works well).
PROFILES=$(cat -)

# For each given profile, print the minimum password length as set by the password policy.
# If the account does not have a password policy set, <min length> will be "no-password-policy".
# Outputs in the following format:
# <profile> <min length>
for PROFILE in $PROFILES; do
    rm ./.pw-policy-err.tmp 2>/dev/null
    LENGTH=$( aws --profile ${PROFILE} iam get-account-password-policy 2>./.pw-policy-err.tmp | jq -r '.PasswordPolicy.MinimumPasswordLength')

    AWSERR=$(cat ./.pw-policy-err.tmp)

    if [ ! -z "${AWSERR}" ] && [[ "${AWSERR}" == *"NoSuchEntity"* ]]; then
        LENGTH="no-password-policy"
    fi

    if [ ! -z "${LENGTH}" ]; then
        echo "$PROFILE $LENGTH"
    fi

done
rm ./.pw-policy-err.tmp 2>/dev/null
