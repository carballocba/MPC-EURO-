#!/bin/sh
set -eu
cd "$(dirname "$0")";. ./common.sh
read_context "$1";owner > "$TX/guardian";touch "$TX/watchdog.ready"
i=0
while [ ! -f "$TX/committed" ]&&[ ! -f "$TX/worker.done" ];do
 if ! alive "$TX/worker" || [ "$i" -ge 180 ];then
  state watchdog-recovery
  if alive "$TX/worker";then
   matches "$TX/worker" || { state recovery-worker-identity-unknown;exit 1; }
   p=$(awk '{print $1}' "$TX/worker");kill -TERM "$p" 2>/dev/null||true;sleep 3
   # If its recovery child owns rollback, do not launch an overlapping recovery.
   if [ -f "$TX/rollback.lock/owner" ]&&alive "$TX/rollback.lock/owner";then
    j=0;while [ -f "$TX/rollback.lock/owner" ] && alive "$TX/rollback.lock/owner";do [ "$j" -lt 300 ]||{ state recovery-owner-timeout;exit 1; };sleep 1;j=$((j+1));done
   fi
   if [ -f "$TX/rollback.done" ];then touch "$TX/worker.done";exit 0;fi
   if alive "$TX/worker";then matches "$TX/worker" || { state recovery-worker-identity-unknown;exit 1; };kill -KILL "$p" 2>/dev/null||true;fi
  fi
  # The lease also protects this path against manual recover.sh and worker EXIT traps.
  sh "$TX/rollback.sh" "$TX";touch "$TX/worker.done"
  exit 0
 fi
 sleep 1;i=$((i+1))
done
