#!/bin/sh
# Start (or restart) the Ghost Mode web server on :8090. Needs the three engines up on 8081-8083.
# The password lives in /root/.qb_env (QB_PASSWORD=...), never in the code.
pkill -f "[s]erver.py" 2>/dev/null; sleep 1
[ -f /root/.qb_env ] && . /root/.qb_env && export QB_PASSWORD
export QB_ENGINES=http://127.0.0.1:8081/v1/chat/completions,http://127.0.0.1:8082/v1/chat/completions,http://127.0.0.1:8083/v1/chat/completions
export QB_CHAIR=${QB_CHAIR:-0}
cd /root && QB_PORT=8090 nohup python3 server.py > /root/qb.log 2>&1 &
sleep 2; cat /root/qb.log
