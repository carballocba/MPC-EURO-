#!/bin/sh
# Child is inert until its exact PID/start identity has been durably recorded.
set -eu
cd "$(dirname "$0")";. ./common.sh
read_context "$1";op=$2;grant=$3;parent=$4
case "$op" in stop|start);;*)exit 1;;esac
i=0
until [ -f "$grant" ];do
 alive "$parent"||exit 1
 [ "$i" -lt 30 ]||exit 1;sleep 1;i=$((i+1))
done
exec systemctl --no-block "$op" "$SERVICE"
