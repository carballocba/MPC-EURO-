#!/bin/sh
set -eu
cd "$(dirname "$0")";. ./common.sh
read_context "$1"
[ ! -f "$TX/rollback.done" ]||exit 0
if lease "$TX/rollback.lock";then :;else r=$?;[ "$r" != 2 ]||exit 0;fail 'rollback owner busy/unresolved';fi
# One owner covers settings, renames and service recovery, including slow systemctl calls.
cleanup() { r=$?;trap - EXIT HUP INT TERM;rm -f "$TX/rollback.lock/owner";rmdir "$TX/rollback.lock" 2>/dev/null||true;exit "$r"; }
trap cleanup EXIT;trap 'exit 1' HUP INT TERM
[ ! -f "$TX/rollback.done" ]||exit 0
state recovering
# @HOOK rollback-owned
cancel_control || { state recovery-control-owner-unknown;exit 1; }
stop_host||{ state recovery-host-stop-failed;exit 1; }
err=0
if [ -f "$TX/register.intent" ];then
 if cmp -s "$SETTINGS" "$TX/settings.before";then :
 elif cmp -s "$SETTINGS" "$TX/settings.after";then cp -p "$TX/settings.before" "$SETTINGS.ghost-restore";mv "$SETTINGS.ghost-restore" "$SETTINGS"
 else
  # Preserve legitimate/new unrelated preferences, reverse ONLY our own still-known GHOST entry.
  awk -v report=ghost -f "$TX/xml_contract.awk" "$SETTINGS" > "$TX/ghost.current"||err=1
  awk -v report=ghost -f "$TX/xml_contract.awk" "$TX/settings.after" > "$TX/ghost.after"
  awk -v report=ghost -f "$TX/xml_contract.awk" "$TX/settings.before" > "$TX/ghost.before"
  if [ "$err" = 0 ]&&cmp -s "$TX/ghost.current" "$TX/ghost.after";then
   mode=remove;[ ! -s "$TX/ghost.before" ]||mode=add
   awk -v mode="$mode" -v file="$TARGET/ghost.so" -v uid=47485354 -v entryfile="$TX/ghost.before" -f "$TX/plugin_list.awk" "$SETTINGS" > "$TX/settings.inverse"
   awk -v report=registry -f "$TX/xml_contract.awk" "$TX/settings.inverse" > /dev/null||err=1
   awk -v mode=remove -v file="$TARGET/ghost.so" -v uid=47485354 -f "$TX/plugin_list.awk" "$SETTINGS" > "$TX/inverse.foreign.before"
   awk -v mode=remove -v file="$TARGET/ghost.so" -v uid=47485354 -f "$TX/plugin_list.awk" "$TX/settings.inverse" > "$TX/inverse.foreign.after"
   cmp -s "$TX/inverse.foreign.before" "$TX/inverse.foreign.after"||err=1
   if [ "$err" = 0 ];then cp -p "$SETTINGS" "$SETTINGS.ghost-restore";cat "$TX/settings.inverse" > "$SETTINGS.ghost-restore";mv "$SETTINGS.ghost-restore" "$SETTINGS";fi
  else err=1;fi
 fi
fi
EXISTED=$(cat "$TX/existed")
if [ -f "$TX/swap.intent" ];then
 # Only our known before/after trees may be moved. Interrupted rename is journaled before mutation.
 if [ -d "$TARGET" ];then
  if [ "$EXISTED" = 1 ]&&verify_tree "$TARGET" "$TX/files.before";then :
  elif verify_tree "$TARGET" "$TX/files.after";then
   [ ! -e "$WORK/failed" ]||fail 'failed candidate already retained; manual review'
   mv "$TARGET" "$WORK/failed"
  else state recovery-files-conflict;err=1;fi
 fi
 if [ ! -e "$TARGET" ]&&[ "$EXISTED" = 1 ];then
  if [ -d "$WORK/original" ]&&verify_tree "$WORK/original" "$TX/files.before";then mv "$WORK/original" "$TARGET"
  elif verify_tree "$TX/backup" "$TX/files.before";then
   [ ! -e "$WORK/restore" ]||remove_work_tree "$WORK/restore"
   cp -a "$TX/backup" "$WORK/restore";verify_tree "$WORK/restore" "$TX/files.before"||fail 'restore copy mismatch';mv "$WORK/restore" "$TARGET"
  else state recovery-backup-invalid;err=1;fi
 fi
 if [ "$EXISTED" = 1 ];then verify_tree "$TARGET" "$TX/files.before"||err=1;else [ ! -e "$TARGET" ]||err=1;fi
fi
# No pre-stop/observed snapshot is ever restored. Before register.intent, settings are untouched.
start_host||err=1
if [ "$err" != 0 ];then state recovery-review-required;exit 1;fi
sync;touch "$TX/rollback.done";state restored
