#!/bin/sh
# Idempotent recovery; -n transactions leave service ownership with caller.
set -eu
TX=$1
[ ! -f "$TX/restored" ] || exit 0
TARGET=$(cat "$TX/target");SETTINGS=$(cat "$TX/settings");SERVICE=$(cat "$TX/service");DEFER=$(cat "$TX/defer");EXISTED=$(cat "$TX/existed")
ctl() { if [ "${MPC_INSTALL_TEST:-}" = 1 ];then echo "$1" >> "${MPC_TEST_LOG:-$TX/service.log}";else systemctl "$1" "$SERVICE";fi; }
[ "$DEFER" = 1 ] || ctl stop
# Only roll back our known registry after-image. Never overwrite concurrent preferences.
if cmp -s "$SETTINGS" "$TX/settings.after";then cp -p "$TX/settings.before" "$SETTINGS.ghost-restore";mv "$SETTINGS.ghost-restore" "$SETTINGS";fi
cmp "$SETTINGS" "$TX/settings.before" || { [ "$DEFER" = 1 ] || ctl start;echo 'Registry conflict; retained evidence' >&2;exit 1; }
if [ -d "$TX/prior-active" ];then
 if [ -e "$TARGET" ];then mv "$TARGET" "$TX/failed-active-$(date +%s)-$$";fi
 mv "$TX/prior-active" "$TARGET"
elif [ "$EXISTED" = 0 ] && [ -f "$TX/swapping" ];then
 [ ! -e "$TARGET" ] || mv "$TARGET" "$TX/failed-active-$(date +%s)-$$"
fi
if [ "$EXISTED" = 1 ];then
 (cd "$TARGET"; find . -type f | LC_ALL=C sort | while IFS= read -r p;do sha256sum "$p";done) > "$TX/files.restored"
 cmp "$TX/files.before" "$TX/files.restored"
else [ ! -e "$TARGET" ];fi
[ "$DEFER" = 1 ] || ctl start
if [ "${MPC_INSTALL_TEST:-}" != 1 ] && [ "$DEFER" = 0 ];then systemctl is-active --quiet "$SERVICE";fi
sync;touch "$TX/restored"
