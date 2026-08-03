#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
pid_file="bot/state/service.pid"

if [[ ! -f "$pid_file" ]]; then
  echo "服务未运行"
  exit 0
fi

pid="$(cat "$pid_file")"
if ! kill -0 "$pid" 2>/dev/null; then
  rm -f "$pid_file"
  echo "服务未运行"
  exit 0
fi

kill "$pid"
for _ in {1..30}; do
  if ! kill -0 "$pid" 2>/dev/null; then
    rm -f "$pid_file"
    echo "服务已停止"
    exit 0
  fi
  sleep 1
done

echo "服务未能在30秒内停止，PID: $pid"
exit 1
