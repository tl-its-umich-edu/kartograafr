#!/bin/bash

# This is Docker and cron centric.

# This is run once on startup when using Docker and cron.  It will
# make the startup environment variables available to cron jobs.  It
# also bundles in last minute container configuration so that the same
# image can be used with configuration file selected at startup time.
# That means fewer images are necessary since final configuration
# doesn't need to be baked in.  This is invoked as the initial startup
# command from the Dockerfile.

# The environment variable and container configuration code could be
# separated if that becomes useful.

# TEST TO SEE IF THIS IS ACCURATE:
#
# Cron scheduling lines that want to pass environment variables on should
# start with .... source $HOME/STARTUP_END_VARS.sh; <cmd>


function capture_env {
    # Gather/format/store the environment variables for later use.
    # (This could be more selective if necessary.)
#    sed 's/$/:80/' ips.txt > new-ips.txt
    #    env | sed 's/^\(.*\)$/export \1/g' > /root/STARTUP_ENV_VARS.sh
    # get env variables and quote the value.
    env | sed 's/^\(.*\)$/export \1/g' \
        | sed 's/=/="/' \
        | sed 's/$/"/' \
         >| /root/STARTUP_ENV_VARS.sh
    chmod a+wr /root/STARTUP_ENV_VARS.sh
}

# Start out with these default settings suitable for this Docker
# application configuration.  These will not be inherited by the cron
# job.

SHELL=/bin/sh
PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
LANG=C.UTF-8
LOG_DIR=/var/log
APP_DIR=/usr/local/apps/kartograafr
SECRETS_DIR=/opt/secrets

# Use a safe default configuration  Allow overriding with
# environment variable.
CONFIG_TYPE=${CONFIG_TYPE:-DEV}

function show_file {
    local SHOW_FILE=$1
    echo "VIEW FILE: ${SHOW_FILE}"
    cat ${SHOW_FILE}
    echo "END OF FILE: ${SHOW_FILE}"
}

function setup_docker {

    echo "CONFIG_TYPE: ${CONFIG_TYPE}"
    
    ## require that a configuration type be specified.
    if [ -z "${CONFIG_TYPE}" ]; then
        echo "Must specify container runtime type via CONFIG_TYPE environment variable: DEV, PROD ...."
        exit 1;
    fi
    
    ######## Use type specific configuration file.
    REQUIRED_FILE=${APP_DIR}/configuration/configOpenShift${CONFIG_TYPE}.py
    if [[ ! -e ${REQUIRED_FILE} ]] ; then
        echo "File does not exist: ${REQUIRED_FILE}"
        exit 1;
    fi

    # Link the type file over any existing config.py file.
    ln -sf ${REQUIRED_FILE} ${APP_DIR}/config.py

    echo "config: ${APP_DIR}/config.py"
    
    #show_file ${APP_DIR}/config.py

    #############################
    ####### Use the configuration type specific cron file.
    REQUIRED_FILE=${APP_DIR}/rootdir_etc_cron.d/kartograafr
    if [[ ! -e ${REQUIRED_FILE}.${CONFIG_TYPE} ]] ; then
        echo "File does not exist: ${REQUIRED_FILE}.${CONFIG_TYPE}"
        exit 1;
    fi
    
    cp ${REQUIRED_FILE}.${CONFIG_TYPE} /etc/cron.d/kartograafr
    crontab /etc/cron.d/kartograafr

    show_file /etc/cron.d/kartograafr

    echo "$0: END OF DOCKER CONFIGURATION SETUP FOR ${CONFIG_TYPE}"

}

# Do it.
capture_env

setup_docker

## run cron in the forground so the container keeps going.
cron -f
#end
