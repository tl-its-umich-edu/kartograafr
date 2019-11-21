#!/bin/bash

# This simple shell script controls whether Kartograafr sends logs by email or not when the application
# is run within a container environment (e.g. OpenShift). If log emails are wanted, SEND_EMAIL
# should be set using the Deployment Config (.yaml).

if [ "${SEND_EMAIL}" == "True" ]; then
  echo "Running Kartograafr WITH email flag"
  python main.py --email
else
  echo "Running Kartograafr WITHOUT email flag"
  python main.py
fi

# The End