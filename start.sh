#!/bin/bash

# This simple shell script controls whether kartograafr sends logs by email or not when the application
# is run within a container environment (e.g. OpenShift). If log emails are wanted, SEND_EMAIL
# should be set using the Deployment Config (.yaml).

if [ "${SEND_EMAIL}" == "True" ]; then
  echo "Running kartograafr WITH email flag"
  python main.py --email
else
  echo "Running kartograafr WITHOUT email flag"
  python main.py
fi
