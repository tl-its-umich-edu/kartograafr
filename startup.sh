#!/bin/bash
# Startup for kartograafr.  This sets up the shell environment explicitly.  That makes running in
# different environments or under cron easier.  In particular the cron shell environment is very
# restricted and to be explicitly managed or there will be mysterious problems when running.

# Command line arguments passed to startup.sh will be passed along to kartograafr.

set -x

# default settings
SHELL=/bin/sh
PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
LANG=C.UTF-8
LOG_DIR=/var/log
APP_DIR=/usr/local/apps/kartograafr
PYTHON=$(which python)

## reset if on mac
if [ $(uname) == Darwin ]; then
    PATH=/usr/local/opt/python/libexec/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
#    PYTHON=$(which python)
    DIR=$(pwd)
    LOG_DIR=$(pwd)
    APP_DIR=$(pwd)
    echo "on Mac";
fi

echo "PYTHON: ${PYTHON} PATH: ${PATH} LOG_DIR: ${LOG_DIR} APP_DIR: ${APP_DIR}"

#echo "Starting $0 with args "$@" at ",$(date) >> /var/log/cron.log 2>&1
echo "Starting $0 with args "$@" at ",$(date) >> ${LOG_DIR}/cron.log 2>&1

### setup a standard environment that will work with cron in docker.


# Run the script, passing along any arguments passed in from caller (cron)
#echo /usr/bin/python /usr/local/apps/kartograafr/main.py "$@" >> /var/log/cron.log 2>&1
#/usr/bin/python /usr/local/apps/kartograafr/main.py "$@"
${PYTHON} ${APP_DIR}/main.py "$@"

#end
