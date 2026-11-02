#!/bin/sh
# Quick Board engine: the llama.cpp server Ollama ships, run directly so all 8 seats decode in parallel.
# Ollama refuses parallel requests for the qwen35 architecture; llama-server itself does not.
pkill -x ollama; pkill -f "llama-server --model"
while [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -gt 1000 ]; do sleep 1; done
SPEC="${SPEC-}"   # speculative drafting measured no faster, so off by default
BLOB=$(ls -S /root/.ollama/models/blobs/sha256-* | head -1)   # the 17 GB weights file
export LD_LIBRARY_PATH=/usr/local/lib/ollama:/usr/local/lib/ollama/cuda_v13:/usr/local/nvidia/lib:/usr/local/nvidia/lib64
export GGML_BACKEND_PATH=/usr/local/lib/ollama/cuda_v13/libggml-cuda.so CUDA_VISIBLE_DEVICES=0
nohup /usr/local/lib/ollama/llama-server --model "$BLOB" --host 127.0.0.1 --port 8081 --no-webui --offline \
  --jinja -np 8 -c 32768 --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 -b 512 -ub 512 \
  $SPEC -ngl 999 --log-disable \
  > /root/engine.log 2>&1 &
for i in $(seq 1 90); do curl -sf http://127.0.0.1:8081/health >/dev/null && python3 /root/warm.py && echo engine-ready && exit 0; sleep 2; done
echo engine-failed; tail -20 /root/engine.log; exit 1
