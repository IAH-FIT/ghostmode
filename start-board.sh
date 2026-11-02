#!/bin/sh
# Start (or restart) the Quick Board web server on :8090. Needs the engine up on :8081.
# The password lives in /root/.qb_env (QB_PASSWORD=...), never in the code.
pkill -f "[s]erver.py" 2>/dev/null; sleep 1
[ -f /root/.qb_env ] && . /root/.qb_env && export QB_PASSWORD
cd /root && QB_PORT=8090 nohup python3 server.py > /root/qb.log 2>&1 &
sleep 2; cat /root/qb.log
