#!/bin/bash
# Run a local debugging smtp server.
# If this fails check to see if one is already running:
#     ps -aef | grep -i localhost
# This script runs in the foreground.  That works great if you invoke it in a separate terminal window. E.G.
#  xterm -e ./runDebugEmail.sh &
set -x
python -m smtpd -d -n -c DebuggingServer localhost:1025
#end
