#!/usr/bin/env bash
# 安装/卸载 watchdog 的 cron 任务（每分钟自愈一次）。
#   bash bot/install-watchdog.sh          # 安装
#   bash bot/install-watchdog.sh --remove # 卸载
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
watchdog="$script_dir/watchdog.sh"
marker="# lark-test-bot-watchdog"
cron_line="* * * * * bash $watchdog $marker"

current="$(crontab -l 2>/dev/null || true)"
# 先剔除旧的 watchdog 行和空行，保证幂等。
filtered="$(printf '%s\n' "$current" | grep -vF "$marker" | grep -v '^[[:space:]]*$' || true)"

if [[ "${1:-}" == "--remove" ]]; then
  if [[ -n "$filtered" ]]; then
    printf '%s\n' "$filtered" | crontab -
  else
    crontab -r 2>/dev/null || true
  fi
  echo "已卸载 watchdog cron 任务"
  exit 0
fi

chmod +x "$watchdog"
if [[ -n "$filtered" ]]; then
  printf '%s\n%s\n' "$filtered" "$cron_line" | crontab -
else
  printf '%s\n' "$cron_line" | crontab -
fi
echo "已安装 watchdog cron 任务（每分钟检测，挂掉自动拉起）："
crontab -l | grep -F "$marker"
