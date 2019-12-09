#!/bin/bash

# This simple shell script performs a couple basic steps to set up the application to run in a container environment
# (e.g. OpenShift). First it sets up a courses directory inside the mounted log volume (if necessary). Then it
# determines whether kartograafr will send logs by email or not; if log emails are wanted, SEND_EMAIL should be set
# using the Deployment Config (.yaml).

mkdir -p /var/log/kartograafr/courses

if [ "${SEND_EMAIL}" == "True" ]; then
  echo "Running kartograafr WITH email flag"
  python main.py --email
else
  echo "Running kartograafr WITHOUT email flag"
  python main.py
fi

# The End
