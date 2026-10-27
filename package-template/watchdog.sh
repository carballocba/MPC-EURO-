#!/bin/sh
set -eu
TX=$1;pid=$(cat "$TX/worker");expected=$(cat "$TX/worker.start");i=0
touch "$TX/watchdog.ready"
while [ ! -f "$TX/done" ] && [ ! -f "$TX/committed" ];do
 actual=$(sed 's/.*) //' "/proc/$pid/stat" 2>/dev/null | awk '{print $20}') || actual=''
 if [ "$actual" != "$expected" ] || [ "$i" -ge 180 ];then
  if [ "$actual" = "$expected" ];then kill -TERM "$pid";sleep 3;[ -f "$TX/done" ] && exit 0;kill -KILL "$pid" 2>/dev/null || true;fi
  sh "$TX/rollback.sh" "$TX";touch "$TX/done";exit
 fi
 sleep 1;i=$((i+1))
done
