#!/bin/sh
set -eu
cd "$(dirname "$0")";. ./common.sh
read_context "$1"
if [ -f "$TX/worker" ]&&alive "$TX/worker";then fail 'installer is still active';fi
if [ -f "$TX/guardian" ]&&alive "$TX/guardian";then fail 'guardian is still active';fi
if [ ! -f "$TX/committed" ]&&[ ! -f "$TX/rollback.done" ];then
 # Unarmed failures cannot have changed the host, plugin or settings.
 if [ ! -f "$TX/armed" ];then touch "$TX/rollback.done";state abandoned-before-arm
 else sh "$TX/rollback.sh" "$TX";fi
fi
# Reap stale global lease atomically, only after interrupted recovery is resolved.
if [ -d "$GLOBAL" ];then
 [ "$(cat "$GLOBAL/transaction")" = "$TX" ]||fail 'global lease belongs to another transaction'
 ! alive "$GLOBAL/owner"||fail 'active global owner'
 mkdir "$GLOBAL/reap"||fail 'another reaper or interrupted reap needs inspection'
 mv "$GLOBAL" "$TX/released-lock-$$"
fi
log "Recovery complete; stale lock resolved separately: $TX"
