#!/data/data/com.termux/files/usr/bin/bash
# Stay4S Eigen AI - Pixel 9a Startup Script
# Primary: Qwen3-4B-Instruct-2507 (2.5GB, Q4_K_M) | Fallback: eigen-cyc6-sft-q4 (1.0GB)
# Usage: sh /sdcard/Download/stay4s-ai.sh [start|stop|chat|status|switch]
# 
# Requirements: Termux + llama.cpp built in ~/llama.cpp/build/
# Models in ~/models/

MODEL_DIR=~/models
SERVER=~/llama.cpp/build/bin/llama-server
PORT=8888
PID_FILE=~/stay4s-ai.pid
LOG_FILE=/sdcard/Download/stay4s-ai-server.log

PRIMARY_MODEL="$MODEL_DIR/qwen3-4b-q4_k_m.gguf"
FALLBACK_MODEL="$MODEL_DIR/cyc6-sft-q4.gguf"
CURRENT_MODEL=""

select_model() {
  if [ -f "$PRIMARY_MODEL" ]; then
    CURRENT_MODEL="$PRIMARY_MODEL"
    echo "PRIMARY: qwen3-4b"
  elif [ -f "$FALLBACK_MODEL" ]; then
    CURRENT_MODEL="$FALLBACK_MODEL"
    echo "FALLBACK: eigen-cyc6"
  else
    echo "ERROR: No model found"
    exit 1
  fi
}

start() {
  if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "Server already running (PID $(cat $PID_FILE))"
    exit 0
  fi
  select_model
  echo "Starting Stay4S AI on port $PORT..."
  $SERVER -m "$CURRENT_MODEL" --port $PORT --host 127.0.0.1 -c 4096 -np 2 --temp 0.7 >> "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  echo "PID: $!"
  echo "Loading model (20s)..."
  sleep 20
  HEALTH=$(curl -s http://127.0.0.1:$PORT/health 2>/dev/null)
  if [ -n "$HEALTH" ]; then
    echo "READY on http://127.0.0.1:$PORT"
  else
    echo "Primary failed, trying fallback..."
    kill $(cat "$PID_FILE") 2>/dev/null
    if [ -f "$FALLBACK_MODEL" ]; then
      CURRENT_MODEL="$FALLBACK_MODEL"
      $SERVER -m "$CURRENT_MODEL" --port $PORT --host 127.0.0.1 -c 2048 -np 1 >> "$LOG_FILE" 2>&1 &
      echo $! > "$PID_FILE"
      sleep 15
      HEALTH=$(curl -s http://127.0.0.1:$PORT/health 2>/dev/null)
      if [ -n "$HEALTH" ]; then
        echo "Fallback READY"
      else
        echo "Both models failed"
      fi
    fi
  fi
}

stop() {
  if [ -f "$PID_FILE" ]; then
    kill $(cat "$PID_FILE") 2>/dev/null
    rm -f "$PID_FILE"
    echo "Stopped"
  else
    echo "Not running"
  fi
}

status() {
  if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "RUNNING (PID $(cat $PID_FILE))"
    curl -s http://127.0.0.1:$PORT/health 2>/dev/null
    echo ""
  else
    echo "STOPPED"
  fi
}

chat() {
  if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "Stay4S AI Chat (typ stop om te stoppen)"
    echo "---"
    while true; do
      echo -n "Jij: "
      read -r MSG
      if [ "$MSG" = "stop" ] || [ "$MSG" = "exit" ]; then break; fi
      if [ -z "$MSG" ]; then continue; fi
      RESPONSE=$(curl -s http://127.0.0.1:$PORT/v1/chat/completions -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"$MSG\"}],\"max_tokens\":200,\"temperature\":0.7}" 2>/dev/null)
      ANSWER=$(echo "$RESPONSE" | python -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])" 2>/dev/null)
      echo "AI: $ANSWER"
      echo ""
    done
  else
    echo "Server not running. Start: sh /sdcard/Download/stay4s-ai.sh start"
  fi
}

switch() {
  echo "Models in $MODEL_DIR:"
  ls -lh $MODEL_DIR/*.gguf 2>/dev/null
}

case "$1" in
  start)  start ;;
  stop)   stop ;;
  chat)   chat ;;
  status) status ;;
  switch) switch ;;
  *)      echo "Usage: $0 {start|stop|chat|status|switch}" ;;
esac