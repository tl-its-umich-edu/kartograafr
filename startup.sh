#!/bin/bash
# Startup script for running kartograafr within a Docker container or
# from a command line. This sets up the shell environment explicitly
# to hide environmental differences.  An explicit setup makes it easy to:
# 1) run in Docker or from the command line with little change,
# 2) simulate the very limited shell environment provided by cron in Docker.

# This currently recognizes Docker and OSX environments.  It does not
# need to distingish between OpenShift and other docker environments.

# Command line arguments passed to startup.sh will be passed along to kartograafr.

#set -x

# Start out with these default settings suitable for Docker.
SHELL=/bin/sh
PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
LANG=C.UTF-8
LOG_DIR=/var/log
APP_DIR=/usr/local/apps/kartograafr
SECRETS_DIR=/opt/secrets

# If running the application directly on OSX command line without
# Docker then localize environment settings and insist on there
# already be an active Python virtual environment.

# On OSX this assumes secrets.py is available in the sub-directory
# ./OPT/SECRETS.  That file can be a symbolic link to a copy elsewhere.

if [ $(uname) == Darwin ]; then
    echo "STARTUP ON OSX"
    if [ -z "${VIRTUAL_ENV}" ]; then
        echo "ERROR: must setup python virtual environment."
        exit 1;
    fi

    # get rid of any existing complied python in case there is a change via symbolic link.
    find . -name \*pyc -delete

    # Use the python virtual environment.
    source ${VIRTUAL_ENV}/bin/activate
    echo "Using python virtual environment: ${VIRTUAL_ENV}"
    # reset environment to the new python and local directories
    DIR=$(pwd)
    LOG_DIR=$(pwd)
    APP_DIR=$(pwd)
    # use local secrets directory.
    SECRETS_DIR=./OPT/SECRETS
fi

# The application's secret/sensitive information is kept in a separate
# directory.  Now make that directory visible to the application.

export PYTHONPATH=${PYTHONPATH}:${SECRETS_DIR}

# find / document the local python
PYTHON=$(which python)

echo "using: PYTHON: ${PYTHON}"
echo "PATH: ${PATH}"
echo "LOG_DIR: ${LOG_DIR}"
echo "APP_DIR: ${APP_DIR}"
echo "PYTHONPATH: [${PYTHONPATH}]"

echo "Starting $0 with args "$@" at ",$(date) >> ${LOG_DIR}/cron.log 2>&1

# Start program script and pass along any arguments supplied to the
# startup script.

${PYTHON} ${APP_DIR}/main.py "$@"

#end
