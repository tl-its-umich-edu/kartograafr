#!/bin/bash
# Startup script for kartograafr.  This sets up the shell environment explicitly.
# That makes it easier to run in different environments.  It sets up a restricted
# environment similar to the cron environment.  This makes it easier to ensure
# the script will run under cron without mystery.

# Currently recognizes Docker, and OSX environments.

# Command line arguments passed to startup.sh will be passed along to kartograafr.

#set -x

# Start out with these default settings.  Assume will run under Docker.
SHELL=/bin/sh
PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
LANG=C.UTF-8
LOG_DIR=/var/log
APP_DIR=/usr/local/apps/kartograafr
#PYTHON=$(which python)
SECRETS_DIR=/opt/secrets

# If running directly on OSX without Docker then localize environment
# and insist on there being an active Python virtual environment.

if [ $(uname) == Darwin ]; then
    echo "STARTUP ON OSX"
    if [ -z "${VIRTUAL_ENV}" ]; then
        echo "ERROR: must setup python virtual environment"
        exit 1;
    fi

    # use the python virtual environment.
    source ${VIRTUAL_ENV}/bin/activate
    echo "Using python virtual environment: ${VIRTUAL_ENV}"
    # reset environment to the new python and local directories
    # PYTHON=$(which python)
    DIR=$(pwd)
    LOG_DIR=$(pwd)
    APP_DIR=$(pwd)
    # use local secrets directory.
    SECRETS_DIR=./OPT/SECRETS

fi

# Secret information is kept in a separate directory.
# Make that directory visible to the application.

export PYTHONPATH=${PYTHONPATH}:${SECRETS_DIR}

# find / document the local python
PYTHON=$(which python)

echo "using: PYTHON: ${PYTHON} PATH: ${PATH}\nLOG_DIR: ${LOG_DIR}\nAPP_DIR: ${APP_DIR}"
echo "PYTHONPATH: [${PYTHONPATH}]"

#echo "ENV in $0"
#env

echo "Starting $0 with args "$@" at ",$(date) >> ${LOG_DIR}/cron.log 2>&1

#echo "USING PYTHON: ${PYTHON} PYTHONPATH: ${PYTHONPATH}"
# Run the script, passing along any arguments passed in from caller (cron)

${PYTHON} ${APP_DIR}/main.py "$@"

#end
