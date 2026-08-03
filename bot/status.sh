#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
pid_file="bot/state/service.pid"

if [[ -f "$pid_file" ]]; then
  pid="$(cat "$pid_file")"
  if kill -0 "$pid" 2>/dev/null; then
    echo "服务运行中，PID: $pid"
    tail -10 bot/logs/service.log
    exit 0
  fi
fi

echo "服务未运行"
exit 1
