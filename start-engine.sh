#!/bin/sh
# Ghost Mode engines: three AIs from three labs, each its own llama.cpp server on this machine's loopback address.
# 8081 Qwen (Alibaba), 8082 Gemma (Google), 8083 Mistral (Mistral AI). Four parallel slots each, 4k tokens a slot.
# --log-disable: the engines log nothing; their output goes nowhere.
pkill -f "llama-server --model"; sleep 2
BIN=/root/llama.cpp/build/bin/llama-server
M=/root/models
start() {  # $1 port, $2 weights file
  nohup $BIN --model "$M/$2" --host 127.0.0.1 --port $1 --no-webui --offline --jinja -np 4 -c 16384 \
    --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 -b 512 -ub 512 -ngl 999 --log-disable > /dev/null 2>&1 &
}
start 8081 Huihui-Qwen3.8-27B-abliterated-UD-DW-Q4_K_M.gguf
start 8082 gemma-4-31B-it-abliterated.Q4_K_M.gguf
start 8083 Huihui-Mistral-Small-3.2-24B-Instruct-2506-abliterated-llamacppfixed.Q4_K_M.gguf
export QB_ENGINES=http://127.0.0.1:8081/v1/chat/completions,http://127.0.0.1:8082/v1/chat/completions,http://127.0.0.1:8083/v1/chat/completions
for i in $(seq 1 150); do
  curl -sf http://127.0.0.1:8081/health >/dev/null && curl -sf http://127.0.0.1:8082/health >/dev/null && curl -sf http://127.0.0.1:8083/health >/dev/null \
    && python3 /root/warm.py && echo engines-ready && exit 0
  sleep 2
done
echo engines-failed; exit 1
