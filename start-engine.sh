#!/bin/sh
# Ghost Mode engines: three AIs from three labs, each its own server on this machine's loopback address.
# Which AIs they are lives in /root/models.conf on the machine. The Verify page gives each weights file's digest, so the check needs no names.
# Four parallel slots each, 4k tokens a slot. Logging is switched off: the engines write nothing, their output goes nowhere.
. /root/models.conf || { echo models.conf missing; exit 1; }   # BIN (engine program), M (weights folder), W1 W2 W3 (weights files)
pkill -f -- "--model $M/"; sleep 2
start() {  # $1 port, $2 weights file
  nohup $BIN --model "$M/$2" --host 127.0.0.1 --port $1 --no-webui --offline --jinja -np 4 -c 16384 \
    --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 -b 512 -ub 512 -ngl 999 --log-disable > /dev/null 2>&1 &
}
start 8081 $W1
start 8082 $W2
start 8083 $W3
export QB_ENGINES=http://127.0.0.1:8081/v1/chat/completions,http://127.0.0.1:8082/v1/chat/completions,http://127.0.0.1:8083/v1/chat/completions
for i in $(seq 1 150); do
  curl -sf http://127.0.0.1:8081/health >/dev/null && curl -sf http://127.0.0.1:8082/health >/dev/null && curl -sf http://127.0.0.1:8083/health >/dev/null \
    && python3 /root/warm.py && echo engines-ready && exit 0
  sleep 2
done
echo engines-failed; exit 1
