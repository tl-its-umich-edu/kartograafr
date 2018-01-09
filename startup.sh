#!/bin/bash
#
# $0 is a single script to setup the shell environment for the
# kartograafr application to run in multiple differetn runtime
# environments (command line or Docker container).
#
# An explicit setup makes it easy to:
# 1) run in Docker or from the command line with little change,
# 2) simulate the very limited shell environment provided by cron in Docker.

# This currently recognizes Docker and OSX environments.  It does not
# need to distingish between OpenShift and other Docker environments.

# Command line arguments passed to startup.sh will be passed along to kartograafr.

# Because of the dependency on the new ESRI ArcGIS Python API the script must be
# run with an Anaconda virtual invironment.  The Dockerfile shows how that can be
# setup for Linux.  An OSX installation can be modeled on that.

## Environment variables.  The USE_CONDA_ENV value must be set when the script is invoked.
### USE_CONDA_ENV - external,required - set to name of the conda environment to use.  E.g. py35
### USE_CONDA_PATH - internal - will be set to the full path of the anaconda environment.
### CONDA_PREFIX - automatic - set by the current external conda environment if one is active.

# set -x
# Terminate if there are any errors.
set -e

# Start out with these default settings suitable for the Docker configuration.
SHELL=/bin/sh
PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
LANG=C.UTF-8
LOG_DIR=/var/log
APP_DIR=/usr/local/apps/kartograafr
SECRETS_DIR=/opt/secrets
USE_CONDA_PATH=/opt/conda

# If running the application directly from OSX command line without
# Docker then modify environment settings.  This assumes that
# secrets.py is available in the local sub-directory ./OPT/SECRETS.  That
# file can be a symbolic link to a copy elsewhere.

function setup_osx {
    echo "STARTUP ON OSX (not Docker) in local file system."

    # get rid of existing complied python cache files in case there
    # was a file change that could be masked by a symbolic link.
    
    find . -name \*pyc -delete

    # reset environment to the OSX appropriate python and local directories
    DIR=$(pwd)
    LOG_DIR=$(pwd)
    APP_DIR=$(pwd)
    # use local secrets directory.
    SECRETS_DIR=./OPT/SECRETS
}

# Chose the run-time environment. This exists as a separate function
# to make it trivial to add new environments if necessary.

function setup_env {

    ### A conda (anaconda) virtual python environment name must be specified.
    if [ -z "${USE_CONDA_ENV}" ]; then
        echo "ERROR: must have conda environment set in USE_CONDA_ENV"
        exit 1;
    fi
    
    # The default setup in script is fine for Docker.  Need to modify
    # paths and directories if running from command line or IDE in OSX.
    if [ $(uname) == Darwin ]; then
        setup_osx
    fi

}

## Run that python code.
function run_app {

    echo "$0: in run_app"

    # Make the non-application directory with secrets available to
    # Python.
    export PYTHONPATH=${PYTHONPATH}:${SECRETS_DIR}

    ##### Activate the conda environment
    
    # if some conda environment is already configured use that existing
    # path that to find the "activate" code.
    
    if [ -n "${CONDA_PREFIX}" ]; then
        USE_CONDA_PATH=${CONDA_PREFIX}
    fi

    # In any case activate the conda environment passed in.
    if [ -n "${USE_CONDA_PATH}" ]; then
        echo "use conda environment ${USE_CONDA_ENV}"
        source ${USE_CONDA_PATH}/bin/activate ${USE_CONDA_ENV}
    fi

    # at this point have the execution environment setup.

    # find and document paths used for the application.
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

############# Setup and then run application ############3
setup_env
run_app

#end
