#!/bin/bash
# Accepts newline delimited AWS profiles from STDIN (piped input works well).
PROFILES=$(cat -)

# For each given profile, find if inline policies are in use and if so, where.
# Outputs in the following format:
# <profile> <resource using inline policies> <number of inline policies>
for PROFILE in $PROFILES; do
    for IAMUSER in $(aws --profile ${PROFILE} iam list-users | jq -r '.Users[] | .UserName'); do
        INLINE_POLICIES=$(aws --profile ${PROFILE} iam list-user-policies \
            --user-name ${IAMUSER} | jq '.PolicyNames | length')

        if [ $INLINE_POLICIES -gt 0 ]; then
            echo "$PROFILE user/$IAMUSER $INLINE_POLICIES"
        fi
    done

    for IAMROLE in $(aws --profile ${PROFILE} iam list-roles | jq -r '.Roles[] | .RoleName'); do
        INLINE_POLICIES=$(aws --profile ${PROFILE} iam list-role-policies \
            --role-name ${IAMROLE} | jq '.PolicyNames | length')

        if [ $INLINE_POLICIES -gt 0 ]; then
            echo "$PROFILE role/$IAMROLE $INLINE_POLICIES"
        fi
    done

    for IAMGROUP in $(aws --profile ${PROFILE} iam list-groups | jq -r '.Groups[] | .GroupName'); do
        INLINE_POLICIES=$(aws --profile ${PROFILE} iam list-group-policies \
            --group-name ${IAMGROUP} | jq '.PolicyNames | length')

        if [ $INLINE_POLICIES -gt 0 ]; then
            echo "$PROFILE group/$IAMGROUP $INLINE_POLICIES"
        fi
    done
done
