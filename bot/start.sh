#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p bot/logs bot/state bot/jobs

if [[ -f bot/state/service.pid ]]; then
  old_pid="$(cat bot/state/service.pid)"
  if kill -0 "$old_pid" 2>/dev/null; then
    echo "服务已运行，PID: $old_pid"
    exit 0
  fi
  rm -f bot/state/service.pid
fi

if [[ -f bot/.env ]]; then
  set -a
  source bot/.env
  set +a
fi

: > bot/logs/service.log
nohup python3 bot/lark_test_bot.py >>bot/logs/service.log 2>&1 </dev/null &
pid=$!
echo "$pid" > bot/state/service.pid

for _ in {1..30}; do
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "服务启动失败："
    tail -40 bot/logs/service.log
    rm -f bot/state/service.pid
    exit 1
  fi
  if tail -30 bot/logs/service.log | grep -q "bot service ready"; then
    echo "服务已启动，PID: $pid"
    exit 0
  fi
  sleep 1
done

echo "服务启动超时，请查看 bot/logs/service.log"
exit 1
