#!/bin/bash
# Replace a secret with give name with contents of given directory.
# Typically will put one file in the source directory.

#set -x

# if not arguments then print help
if [ $# -eq 0 ]; then
    echo "$0: <SECRET_NAME> <DIRECTORY> "
    echo "Upload secrets to current OS project."
    echo "Must supply name that OS will use as the volume name "
    echo "and the path to the directory containing the secrets file(s)."
    exit 1
fi

set -u

######## set the arguments
SECRET_NAME=$1
if [ -z "${SECRET_NAME}" ]; then
    echo "Need to set the OpenShift name of the secret."
    exit 1;
fi

SRC_NAME=$2
if [ -z "${SRC_NAME}" ]; then
    echo "Need to set the source directory name."
    exit 1;
fi

######## redo the secret
# delete old secret.
oc delete secret ${SECRET_NAME}
set -e
# recreate secret with new value.
oc create secret generic ${SECRET_NAME} --from-file=${SRC_NAME}
#end
