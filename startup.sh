#!/bin/bash
#
# This is a single script to manage invoking kartograafr in different environments
# including OSX command line and Docker.  kartograafr can be run directly from
# Eclipse without this script.
#
# $0 will startup the kartograafr application making minor adjustments to the
# run time environment (command line or Docker container).  It doesn't need to do much
# for Docker since that is the default configuration. This doesn't modify the container.

# A startup script for kartograafr is useful to hide differences between
# running locally from the command line or within a Docker container.
# This sets up the shell environment explicitly to hide environmental differences.
# An explicit setup makes it easy to:
# 1) run in Docker or from the command line with little change,
# 2) simulate the very limited shell environment provided by cron in Docker.

# This currently recognizes Docker and OSX environments.  It does not
# need to distingish between OpenShift and other Docker environments.

# Command line arguments passed to startup.sh will be passed along to kartograafr.

# set -x
# Terminate if there are any errors.
set -e

# Start out with these default settings suitable for Docker.
SHELL=/bin/sh
PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
LANG=C.UTF-8
LOG_DIR=/var/log
APP_DIR=/usr/local/apps/kartograafr
SECRETS_DIR=/opt/secrets

# If running the application directly from OSX command line without
# Docker then modify environment settings and insist on there
# already be an active Python virtual environment.
# This assumes that secrets.py is available in the sub-directory
# ./OPT/SECRETS.  That file can be a symbolic link to a copy elsewhere.

function setup_osx {
    echo "STARTUP ON OSX (not Docker) in local file system."
    if [ -z "${VIRTUAL_ENV}" ]; then
        echo "ERROR: must setup python virtual environment."
        exit 1;
    fi

    # get rid of any existing complied python in case there was a change masked
    # by a symbolic link.
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
}

# Chose the run-time environment. This exists as a function to make it
# trivial to add new environments if necessary.

function setup_env {

    # Default setup is fine for Docker.  Need to modify paths 
    # and directories if running directly in OSX.
    if [ $(uname) == Darwin ]; then
        setup_osx
    fi
}

## invoke the python code.
function run_app {
    # The application's secret/sensitive information is kept in a separate
    # directory.  Now make that directory visible to the application.

    echo "$0: in run_app"

    # Make the directory with secrets available to Python.
    export PYTHONPATH=${PYTHONPATH}:${SECRETS_DIR}

USE_CONDA_BIN=/opt/conda/bin
##### see if need to activate conda environment
if [ -n "${USE_CONDA_ENV}" ]; then
    echo "use conda environment ${USE_CONDA_ENV}"
    source ${USE_CONDA_BIN}/activate ${USE_CONDA_ENV}
fi


#### at this point have the executible environment setup be it
# venv or conda or default.
####

### ????
# The application's secret/sensitive information is kept in a separate
# directory.  Now make that directory visible to the application.
### ????

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
}


############# Setup then run application ############3
setup_env
run_app

#end
