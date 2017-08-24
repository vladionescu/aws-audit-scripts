#!/bin/bash
# Accepts newline delimited AWS profiles from STDIN (piped input works well).
PROFILES=$(cat -)

# For each given profile, find IAM Users with no console or API activity.
# Outputs in the following format:
# <profile> <IAM User>
for PROFILE in $PROFILES; do
    for IAMUSER in $(aws --profile ${PROFILE} iam list-users | jq -r '.Users[].UserName'); do
        # If an IAM User doesn't have a password set, get-login-profile fails with NoSuchEntity and aws returns 255
        aws --profile ${PROFILE} iam get-login-profile --user-name ${IAMUSER} >/dev/null 2>&1
        if [ $? -eq 255 ]; then
            HAS_PW=0
        else
            HAS_PW=1
        fi

        ACCESS_KEYS=$(aws --profile ${PROFILE} iam list-access-keys --user-name ${IAMUSER} 2>/dev/null | jq -r '.AccessKeyMetadata[].AccessKeyId')
        if [ ! -z "${ACCESS_KEYS}" ]; then
            HAS_KEYS=1
        else
            HAS_KEYS=0
        fi

        if [ $HAS_PW -eq 0 ] && [ $HAS_KEYS -eq 0 ]; then
            # This shouldn't happen. An IAM User must have either keys or password.
            echo "[Error] No password or keys for: $PROFILE $IAMUSER" >&2
        elif [ $HAS_PW -eq 1 ] && [ $HAS_KEYS -eq 1 ]; then
            # Both password and keys are set. If neither have ever been used, report the account.
            PW_LASTUSE=$(aws --profile ${PROFILE} iam get-user --user-name ${IAMUSER} 2>/dev/null | jq -rM '.User.PasswordLastUsed')
            if [ "${PW_LASTUSE}" == "null" ] || [ -z "${PW_LASTUSE}" ]; then
                for KEY in $ACCESS_KEYS; do
                    KEY_LASTUSE=$(aws --profile ${PROFILE} iam get-access-key-last-used --access-key-id ${KEY} | jq -rM '.AccessKeyLastUsed.LastUsedDate')
                    if [ "${KEY_LASTUSE}" == "null" ] || [ -z "${KEY_LASTUSE}" ]; then
                        REPORT=1
                    else
                        REPORT=0
                    fi
                done

                if [ $REPORT -eq 1 ]; then
                    echo "$PROFILE $IAMUSER"
                fi
            fi
        elif [ $HAS_PW -eq 1 ]; then
            # Only a password is set. If it hasn't been used, report the account.
            PW_LASTUSE=$(aws --profile ${PROFILE} iam get-user --user-name ${IAMUSER} 2>/dev/null | jq -rM '.User.PasswordLastUsed')
            if [ "${PW_LASTUSE}" == "null" ] || [ -z "${PW_LASTUSE}" ]; then
                echo "$PROFILE $IAMUSER"
            fi
        elif [ $HAS_KEYS -eq 1 ]; then
            # Only keys are set. If they haven't been used, report the account.
            for KEY in $ACCESS_KEYS; do
                KEY_LASTUSE=$(aws --profile ${PROFILE} iam get-access-key-last-used --access-key-id ${KEY} | jq -rM '.AccessKeyLastUsed.LastUsedDate')
                if [ "${KEY_LASTUSE}" == "null" ] || [ -z "${KEY_LASTUSE}" ]; then
                    REPORT=1
                else
                    REPORT=0
                fi
            done

            if [ $REPORT -eq 1 ]; then
                echo "$PROFILE $IAMUSER"
            fi
        fi
    done
done
