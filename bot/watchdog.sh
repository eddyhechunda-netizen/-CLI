#!/usr/bin/env bash
# 守护脚本：检测机器人服务是否存活，挂掉则自动拉起。
# 由 cron 每分钟调用（见 install-watchdog.sh），或手动执行。
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
cd "$repo_root"

pid_file="bot/state/service.pid"
lock_file="bot/state/watchdog.lock"
log_file="bot/logs/watchdog.log"
log_file_service="bot/logs/service.log"
mkdir -p bot/state bot/logs

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >>"$log_file"; }

restart_stamp="bot/state/last_clean_restart"
# 启动后至少运行这么久才做健康检测，给 websocket 建连留时间。
HEALTH_MIN_UPTIME="${LARK_TEST_BOT_HEALTH_MIN_UPTIME:-90}"
# 干净重启后的冷却期（秒），避免网络真断时反复重启。
CLEAN_RESTART_COOLDOWN="${LARK_TEST_BOT_CLEAN_RESTART_COOLDOWN:-300}"

# 判断“假在线”：进程存活但 websocket 未真正连接。
# 返回 0=健康；1=疑似假在线。依据当前进程的 service.log（start.sh 每次覆盖，窗口即本进程）：
#   - 从未出现 `feishu-websocket: connected` → 假在线；
#   - 最近一次连接失效信号（网络恢复重建/连接 rebuilt/stdin closed/NetworkError 等）晚于
#     最后一次 connected，且其后没有新的 connected → 重连未成功，假在线。
health_ok() {
  local log_path="$1"
  [[ -f "$log_path" ]] || return 0
  local last_conn last_fail
  last_conn="$(grep -n "feishu-websocket: connected" "$log_path" | tail -1 | cut -d: -f1)"
  last_fail="$(grep -nE "network recovered; rebuilding|Feishu event connection rebuilt|stdin closed — shutting down|NetworkError|server misbehaving|connection refused|TLS handshake timeout|429" "$log_path" | tail -1 | cut -d: -f1)"
  if [[ -z "$last_conn" ]]; then
    return 1
  fi
  if [[ -n "$last_fail" && "$last_fail" -gt "$last_conn" ]]; then
    return 1
  fi
  return 0
}

# 干净重启：停服务 + 清事件总线陈旧订阅 + 重新启动，并记录时间戳。
clean_restart() {
  log "fake-online detected (process alive but websocket not truly connected); clean restart"
  bash bot/stop.sh >>"$log_file" 2>&1 || true
  lark-cli event stop --json >>"$log_file" 2>&1 || true
  if bash bot/start.sh >>"$log_file" 2>&1; then
    date +%s >"$restart_stamp"
    local np
    np="$(cat "$pid_file" 2>/dev/null || echo '?')"
    log "clean restart ok, pid=$np"
  else
    log "clean restart FAILED (see service.log)"
  fi
}

# cron 的最小 PATH 找不到 nvm 里的 lark-cli，这里补齐 node/bin 目录。
for nb in "$HOME"/.nvm/versions/node/*/bin; do
  [[ -d "$nb" ]] && PATH="$nb:$PATH"
done
export PATH


# flock 防止多个 watchdog 实例并发拉起，重叠时直接退出。
exec 9>"$lock_file"
if ! flock -n 9; then
  exit 0
fi

running=0
pid=""
if [[ -f "$pid_file" ]]; then
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
    running=1
  fi
fi

# 情况一：进程不存在 → 直接拉起（保留原行为）。
if [[ "$running" -eq 0 ]]; then
  log "service not running; restarting via start.sh"
  if bash bot/start.sh >>"$log_file" 2>&1; then
    new_pid="$(cat "$pid_file" 2>/dev/null || echo '?')"
    log "restart ok, pid=$new_pid"
  else
    log "restart FAILED (see service.log)"
  fi
  exit 0
fi

# 情况二：进程存活 → 检测“假在线”。
uptime_s="$(ps -o etimes= -p "$pid" 2>/dev/null | tr -d ' ' || echo 0)"
[[ -z "$uptime_s" ]] && uptime_s=0
# 刚启动不足 HEALTH_MIN_UPTIME 秒，给 websocket 建连留时间，暂不判定。
if [[ "$uptime_s" -lt "$HEALTH_MIN_UPTIME" ]]; then
  exit 0
fi

if health_ok "$log_file_service"; then
  exit 0
fi

# 疑似假在线：先看冷却，避免网络真断时反复干净重启。
now="$(date +%s)"
if [[ -f "$restart_stamp" ]]; then
  last="$(cat "$restart_stamp" 2>/dev/null || echo 0)"
  if [[ -n "${last:-}" ]] && (( now - last < CLEAN_RESTART_COOLDOWN )); then
    log "fake-online suspected but within cooldown ($((now - last))s < ${CLEAN_RESTART_COOLDOWN}s); skip"
    exit 0
  fi
fi

clean_restart
