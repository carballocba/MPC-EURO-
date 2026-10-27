#!/bin/sh
# GHOST-only, POSIX device installer. Official interface: -y [-n] [-t Synths].
set -eu
cd "$(dirname "$0")"
ACTION=${GHOST_ACTION:-install}; SYNTHS=/sdcard/Synths; YES=0; DEFER=0
while [ $# -gt 0 ]; do case "$1" in -y) YES=1;shift;; -n) DEFER=1;shift;; -t) SYNTHS=$2;shift 2;; *) echo 'usage: install.sh/uninstall.sh [-y] [-n] [-t /Synths]' >&2;exit 1;; esac; done
fail() { echo "REFUSED: $*" >&2; exit 1; }
case "$SYNTHS" in /*) ;; *) fail 'absolute Synths path required';; esac
case "$SYNTHS" in *'..'*|*'&'*|*'|'*|*'\'*|*'
'*) fail 'unsupported path';; esac
for x in awk sed sha256sum cp mv cmp find sort mkdir rm date sync cut grep head touch cat dirname; do command -v "$x" >/dev/null || fail "missing $x"; done
[ "${MPC_INSTALL_TEST:-}" = 1 ] || { [ "$(id -u)" = 0 ] && [ "$(uname -m)" = armv7l ]; } || fail 'root ARMv7 required'
SETTINGS=${MPC_SETTINGS:-$(ls /media/az01-internal/Settings/*/MPC.settings /data/Settings/*/MPC.settings 2>/dev/null | head -n 1)}
[ -f "$SETTINGS" ] && [ ! -L "$SETTINGS" ] || fail 'settings missing or symbolic'
[ -d "$SYNTHS" ] && [ ! -L "$SYNTHS" ] || fail 'Synths missing or symbolic'
SYNTHS_INPUT=$SYNTHS
SYNTHS=$(cd "$SYNTHS" && pwd -P)
SKIN='MPC-EURO - VST - GHOST'; TARGET="$SYNTHS/$SKIN"; FILE="$TARGET/ghost.so"
[ ! -L "$TARGET" ] || fail 'symbolic target'
sha256sum -c SHA256SUMS >/dev/null || fail 'package integrity'
if [ "$YES" = 0 ]; then printf 'Save your project. Modify only GHOST and its registry? [y/N] ';read -r ans;[ "$ans" = y ] || exit 1;fi
SERVICE=acvs
if [ "${MPC_INSTALL_TEST:-}" != 1 ]; then
 command -v systemctl >/dev/null || fail 'missing systemctl'
 command -v nohup >/dev/null || fail 'missing nohup'
 systemctl cat acvs >/dev/null 2>&1 || SERVICE=inmusic-mpc
 if [ "$DEFER" = 1 ]; then ! pidof MPC >/dev/null || fail '-n requires stopped host'; else systemctl is-active --quiet "$SERVICE" || fail 'host inactive';fi
fi
LOCK="$SYNTHS/.ghost-installer-lock";mkdir "$LOCK" || fail 'another transaction or recovery lock exists'
TX="$SYNTHS/.ghost-recovery/community-$(date -u +%Y%m%dT%H%M%SZ)-$$";mkdir -p "$TX"
trap 'rm -f "$LOCK/transaction"; rmdir "$LOCK" 2>/dev/null || true' EXIT
trap 'exit 1' HUP INT TERM
echo "$TX" > "$LOCK/transaction"; echo "Recovery: $TX"
# Immutable snapshots/checkpoints stay outside the replaced directory and are never auto-deleted.
cp -p "$SETTINGS" "$TX/settings.before"
[ ! -d "$TARGET" ] || cp -a "$TARGET" "$TX/backup"
EXISTED=0;[ ! -d "$TARGET" ] || EXISTED=1
hash() { sha256sum "$1" | cut -c 1-64; }
inventory() { (cd "$1"; find . -type f | LC_ALL=C sort | while IFS= read -r p;do sha256sum "$p";done); }
if [ "$EXISTED" = 1 ]; then
 [ -z "$(find "$TARGET" ! -type d ! -type f -print)" ] || fail 'symlinks require review'
 inventory "$TARGET" > "$TX/files.before";inventory "$TX/backup" > "$TX/files.backup";cmp "$TX/files.before" "$TX/files.backup" || fail 'backup mismatch'
fi
cp transaction.sh "$TX/transaction.source";cp rollback.sh "$TX/rollback.sh"
printf '%s\n' "$TARGET" > "$TX/target";printf '%s\n' "$SETTINGS" > "$TX/settings";printf '%s\n' "$SERVICE" > "$TX/service";echo "$DEFER" > "$TX/defer";echo "$EXISTED" > "$TX/existed"
# Full old directory is renamed only after a verified staged copy exists.
STAGE="$TX/stage";mkdir "$STAGE"
[ "$EXISTED" = 0 ] || cp -a "$TARGET/." "$STAGE/"
OWN=legacy-owned.sha256
[ ! -f "$TARGET/.ghost-owned.sha256" ] || OWN="$TARGET/.ghost-owned.sha256"
# Remove only byte-identical previously owned files. Modified/unknown user files survive.
if [ "$EXISTED" = 1 ];then
 while IFS= read -r row;do
  h=${row%% *}; p=${row#*  }
  case "$p" in ''|/*|*'..'*|*'
'*) fail 'unsafe ownership record';;esac
  [ ! -f "$STAGE/$p" ] || { [ "$(hash "$STAGE/$p")" != "$h" ] || rm "$STAGE/$p"; }
 done < "$OWN"
fi
rm -f "$STAGE/.ghost-owned.sha256"
if [ "$ACTION" = install ];then
 while IFS= read -r row;do
  h=${row%% *};p=${row#*  }
  if [ -e "$STAGE/$p" ];then
   # User data wins; differing runtime/skin collisions require explicit review.
   case "$p" in Presets/*|'Preset Library/'*|'Performance Presets/'*) continue;; *) fail "modified/unknown package collision: $p";;esac
  fi
  mkdir -p "$(dirname "$STAGE/$p")";cp -p "portable/$SKIN/$p" "$STAGE/$p"
 done < payload.sha256
 cp payload.sha256 "$STAGE/.ghost-owned.sha256"
fi
[ "${GHOST_FAILPOINT:-}" != copy ] || fail 'injected copy failure'
# Retain official BusyBox registry editor; prove non-GHOST content remains unchanged.
sed "s|%payload-path%|$SYNTHS|g" "portable/$SKIN/plugin-meta.xml" > "$TX/entry"
MODE=add;[ "$ACTION" != uninstall ] || MODE=remove
awk -v mode="$MODE" -v file="$FILE" -v uid=47485354 -v entryfile="$TX/entry" -f plugin_list.awk "$SETTINGS" > "$TX/settings.after"
awk -v mode=remove -v file="$FILE" -v uid=47485354 -f plugin_list.awk "$SETTINGS" > "$TX/foreign.before"
awk -v mode=remove -v file="$FILE" -v uid=47485354 -f plugin_list.awk "$TX/settings.after" > "$TX/foreign.after"
! grep -F -e "file=\"$TARGET/" -e "file=\"$SYNTHS_INPUT/$SKIN/" "$TX/foreign.before" >/dev/null || fail 'foreign plugin inside GHOST directory'
cmp "$TX/foreign.before" "$TX/foreign.after" || fail 'foreign registry/preferences changed'
grep -q '</PROPERTIES>' "$TX/settings.after" || fail 'invalid settings root'
n=$(grep -c ' uid="47485354"' "$TX/settings.after" || true)
if [ "$ACTION" = install ];then [ "$n" = 1 ];else [ "$n" = 0 ];fi || fail 'registry count'
[ "${GHOST_FAILPOINT:-}" != registry ] || fail 'injected registration failure'
# Every pre-mutation failure releases lock but retains exact snapshots.
cp watchdog.sh "$TX/watchdog.sh"
echo "$$" > "$TX/worker"
if [ "${MPC_INSTALL_TEST:-}" != 1 ];then sed 's/.*) //' /proc/$$/stat | awk '{print $20}' > "$TX/worker.start";fi
sync
ARMED=0;WATCH=''
finish() {
 rc=$?;trap - EXIT HUP INT TERM
 if [ "$ARMED" = 1 ] && [ ! -f "$TX/committed" ];then
  if sh "$TX/rollback.sh" "$TX";then echo 'Rollback verified';else echo "RECOVERY REQUIRED: $TX" >&2;exit 90;fi
 fi
 touch "$TX/done"
 [ -z "$WATCH" ] || wait "$WATCH" || true
 rmdir "$LOCK" 2>/dev/null || { rm -f "$LOCK/transaction";rmdir "$LOCK"; }
 exit "$rc"
}
trap finish EXIT
trap 'exit 1' HUP INT TERM
cmp "$SETTINGS" "$TX/settings.before" || fail 'concurrent settings change'
if [ "$EXISTED" = 1 ];then inventory "$TARGET" > "$TX/files.now";cmp "$TX/files.before" "$TX/files.now" || fail 'concurrent files change';fi
ARMED=1;touch "$TX/armed"
if [ "${MPC_INSTALL_TEST:-}" != 1 ];then nohup sh "$TX/watchdog.sh" "$TX" </dev/null > "$TX/watchdog.log" 2>&1 & WATCH=$!
 i=0;while [ ! -f "$TX/watchdog.ready" ] && [ "$i" -lt 5 ];do kill -0 "$WATCH" || fail 'watchdog exited';sleep 1;i=$((i+1));done
 [ -f "$TX/watchdog.ready" ] || fail 'watchdog unavailable'
fi
ctl() {
 if [ "${MPC_INSTALL_TEST:-}" = 1 ];then echo "$1" >> "${MPC_TEST_LOG:-$TX/service.log}";else systemctl "$1" "$SERVICE";fi
}
if [ "$DEFER" = 0 ];then ctl stop;fi
if [ "${MPC_INSTALL_TEST:-}" != 1 ];then ! pidof MPC >/dev/null || fail 'host remains running';fi
cmp "$SETTINGS" "$TX/settings.before" || fail 'settings changed while stopping host'
[ "${GHOST_FAILPOINT:-}" != stopped ] || fail 'injected stopped failure'
# Original is retained until explicit user cleanup, never destroyed.
touch "$TX/swapping"
if [ "$EXISTED" = 1 ];then mv "$TARGET" "$TX/prior-active";fi
[ "${GHOST_FAILPOINT:-}" != renamed ] || fail 'injected rename failure'
mv "$STAGE" "$TARGET";touch "$TX/activated"
[ "${GHOST_FAILPOINT:-}" != activated ] || fail 'injected activation failure'
# Stage settings adjacent to original so final rename is atomic on its filesystem.
cp -p "$TX/settings.before" "$SETTINGS.ghost-new"
cat "$TX/settings.after" > "$SETTINGS.ghost-new"
cmp "$SETTINGS" "$TX/settings.before" || fail 'concurrent registry change'
if ! cmp -s "$SETTINGS" "$TX/settings.after";then mv "$SETTINGS.ghost-new" "$SETTINGS";else rm "$SETTINGS.ghost-new";fi
touch "$TX/registered"
[ "${GHOST_FAILPOINT:-}" != registered ] || fail 'injected post-register failure'
if [ "$ACTION" = install ];then
 # Preserved user presets may intentionally differ; every runtime file must match.
 while IFS= read -r row;do h=${row%% *};p=${row#*  };case "$p" in Presets/*|'Preset Library/'*|'Performance Presets/'*) continue;;esac
 [ "$(hash "$TARGET/$p")" = "$h" ] || fail "installed hash: $p"
 done < payload.sha256
fi
cmp "$SETTINGS" "$TX/settings.after" || fail 'post registry integrity'
if [ "$DEFER" = 0 ];then
 ctl start
 if [ "${MPC_INSTALL_TEST:-}" != 1 ];then
  systemctl is-active --quiet "$SERVICE" || fail 'host start failed'
  pid=$(systemctl show -p MainPID --value "$SERVICE");restarts=$(systemctl show -p NRestarts --value "$SERVICE");[ "$pid" != 0 ] || fail 'no host pid'
  sleep 5
  [ "$pid" = "$(systemctl show -p MainPID --value "$SERVICE")" ] && [ "$restarts" = "$(systemctl show -p NRestarts --value "$SERVICE")" ] && systemctl is-active --quiet "$SERVICE" || fail 'unstable host'
 fi
fi
[ "${GHOST_FAILPOINT:-}" != started ] || fail 'injected post-start failure'
sync;touch "$TX/committed";echo "GHOST transaction complete. Backup/recovery: $TX"
