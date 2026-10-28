#!/bin/sh
set -eu
cd "$(dirname "$0")"
. ./common.sh
ACTION=${GHOST_ACTION:-install};SYNTHS=/sdcard/Synths;DEFER=${DEFER:-0};YES=0
case "$DEFER" in 0|1);;*)fail 'invalid deferred state';;esac
while [ $# -gt 0 ];do case "$1" in -y)YES=1;shift;;-n)DEFER=1;shift;;-t)[ $# -ge 2 ]||fail '-t requires path';SYNTHS=$2;shift 2;;*)fail 'usage: [-y] [-n] [-t /Synths]';;esac;done
[ -z "${MPC_INSTALL_TEST:-}" ] || fail 'production installer refuses MPC_INSTALL_TEST'
[ -z "${GHOST_FAILPOINT:-}" ] || fail 'production installer refuses failpoint environment'
case "$ACTION" in install|uninstall);;*)fail 'invalid action';;esac
for c in awk sed sha256sum cp mv cmp find sort mkdir rm date sync cut grep head touch cat dirname basename stat df du mktemp chmod wc tr systemctl nohup pidof id uname kill sleep;do command -v "$c" >/dev/null||fail "missing $c";done
[ "$(id -u)" = 0 ] && [ "$(uname -m)" = armv7l ] || fail 'root Gen1 ARMv7 required'
[ -n "$(proc_id $$)" ] || fail 'process identity unavailable'
[ -r /proc/sys/kernel/random/boot_id ] || fail 'boot identity unavailable'
safe_path "$SYNTHS" && [ -d "$SYNTHS" ] && [ ! -L "$SYNTHS" ] || fail 'invalid/missing Synths directory'
SYNTHS=$(canon "$SYNTHS");SKIN='MPC-EURO - VST - GHOST';TARGET="$SYNTHS/$SKIN";FILE="$TARGET/ghost.so"
[ ! -L "$TARGET" ] && { [ ! -e "$TARGET" ]||[ -d "$TARGET" ]; } || fail 'unexpected target'
SETTINGS=${MPC_SETTINGS:-$(ls /media/az01-internal/Settings/*/MPC.settings /data/Settings/*/MPC.settings 2>/dev/null | head -n 1)}
safe_path "$SETTINGS" && [ -f "$SETTINGS" ] && [ ! -L "$SETTINGS" ] || fail 'invalid settings'
mount_check "$SYNTHS" exec && mount_check "$(dirname "$SETTINGS")" write || fail 'unsupported readonly/noexec mount'
check_names . || fail 'package special files/unsafe names'
sha256sum -c SHA256SUMS >/dev/null || fail 'package checksum'
manifest_paths SHA256SUMS || fail 'unsafe checksum paths'
listed=$(mktemp);actual=$(mktemp)
awk '{print substr($0,67)}' SHA256SUMS | LC_ALL=C sort > "$listed"
find . -type f | sed 's|^./||' | grep -v '^SHA256SUMS$' | LC_ALL=C sort > "$actual"
cmp -s "$listed" "$actual" || { rm -f "$listed" "$actual"; fail 'unlisted or missing package files'; }
rm -f "$listed" "$actual"
manifest_paths payload.sha256 && manifest_paths legacy-owned.sha256 || fail 'invalid package ownership list'
[ "$(hash "portable/$SKIN/ghost.so")" = 588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd ] || fail 'wrong audio binary'
awk -v report=registry -f xml_contract.awk "$SETTINGS" >/dev/null || fail 'unsupported/invalid XML'
RECOVERY=${GHOST_RECOVERY_ROOT:-};WORKROOT=${GHOST_WORK_ROOT:-$RECOVERY}
for p in "$RECOVERY" "$WORKROOT";do safe_path "$p" && [ -d "$p" ] && [ ! -L "$p" ] || fail 'explicit existing recovery/work roots required';done
RECOVERY=$(canon "$RECOVERY");WORKROOT=$(canon "$WORKROOT")
for p in "$RECOVERY" "$WORKROOT";do
 [ "$(stat -c %u "$p")" = 0 ] || fail 'recovery/work roots must be root-owned'
 mode=$(stat -c %a "$p");case "$mode" in *[2367][0-7]|*[0-7][2367]) fail 'recovery/work roots must not be group/world writable';;esac
done
# Validate all configured locations; unknown configuration refuses, never assumes hidden folders are safe.
CONTENT=$(mktemp);trap 'rm -f "$CONTENT"' EXIT
awk -v report=locations -f xml_contract.awk "$SETTINGS" > "$CONTENT" || fail 'cannot parse content roots'
[ -s "$CONTENT" ] || fail 'missing SynthContentLocations'
printf '%s\n' "$SYNTHS" >> "$CONTENT"
outside_content "$RECOVERY" && outside_content "$WORKROOT" || fail 'recovery/work root overlaps a discovery path'
mount_check "$RECOVERY" write && mount_check "$WORKROOT" write || fail 'readonly recovery/work mount'
[ "$(stat -c %d "$WORKROOT")" = "$(stat -c %d "$SYNTHS")" ] || fail 'work root must share target filesystem'
SERVICE=acvs;systemctl cat acvs >/dev/null 2>&1 || SERVICE=inmusic-mpc
if [ "$DEFER" = 0 ];then systemctl is-active --quiet "$SERVICE" && pidof MPC >/dev/null || fail 'host inactive';else ! pidof MPC >/dev/null || fail '-n requires stopped host';fi
[ "$YES" = 1 ] || { printf 'Save project. Continue GHOST-only %s? [y/N] ' "$ACTION";read -r a;[ "$a" = y ]||exit 1; }
# Managed namespaces never adopt pre-existing user folders.
for p in "$RECOVERY/ghost-community-v2" "$WORKROOT/ghost-work-v2";do
 if [ ! -e "$p" ];then mkdir "$p";chmod 700 "$p";printf '%s\n' ghost-installer-2 > "$p/format";fi
 [ ! -L "$p" ] && [ "$(stat -c %u "$p")" = 0 ] && [ "$(stat -c %a "$p")" = 700 ] && [ "$(cat "$p/format")" = ghost-installer-2 ] || fail 'unowned recovery/work namespace'
done
BASE="$RECOVERY/ghost-community-v2";WBASE="$WORKROOT/ghost-work-v2";GLOBAL="$BASE/active.lock"
# Stale lock: resolve old transaction before taking a new one. Never remove an active/reused-PID lease.
if ! mkdir "$GLOBAL" 2>/dev/null;then
 [ -f "$GLOBAL/owner" ] && [ -f "$GLOBAL/transaction" ] || fail 'uninitialized lock: manual inspection required'
 ! alive "$GLOBAL/owner" || fail 'active installer owns lock'
 oldtx=$(cat "$GLOBAL/transaction");case "$oldtx" in "$BASE"/tx-*) ;;*)fail 'unsafe stale transaction';;esac
 [ ! -f "$oldtx/guardian" ] || ! alive "$oldtx/guardian" || fail 'guardian recovery in progress'
 sh "$oldtx/recover.sh" "$oldtx" || fail 'incomplete old transaction requires recovery'
 mkdir "$GLOBAL" || fail 'another installer acquired lock'
fi
owner > "$GLOBAL/owner"
TX='';ARMED=0;WATCH=''
finish() {
 rc=$?;trap - EXIT HUP INT TERM
 if [ -n "$TX" ];then
  if [ "$ARMED" = 1 ] && [ ! -f "$TX/committed" ];then sh "$TX/rollback.sh" "$TX" || { log "RECOVERY REQUIRED $TX";exit 90; };fi
  if [ "$ARMED" = 0 ] && [ -f "$TX/context.ready" ];then touch "$TX/rollback.done";state aborted-before-arm;fi
  touch "$TX/worker.done"
  [ -z "$WATCH" ] || wait "$WATCH" || true
  # Release only after successful recovery/commit, including pre-arm safe failures.
  if [ -f "$TX/committed" ] || [ -f "$TX/rollback.done" ] || [ "$ARMED" = 0 ];then release_global || true;fi
 else rm -f "$GLOBAL/owner";rmdir "$GLOBAL";fi
 rm -f "$CONTENT";exit "$rc"
}
trap finish EXIT;trap 'exit 1' HUP INT TERM
# Bounded by refusal, never implicit deletion of older user-containing backups.
count=$(find "$BASE" -maxdepth 1 -type d -name 'tx-*' | wc -l | tr -d ' ')
[ "$count" -lt 3 ] || fail 'three retained transactions: export/cleanup completed backups first'
used=$(kb "$BASE");[ "$used" -lt 524288 ] || fail 'recovery quota 512 MiB reached'
oldkb=0;if [ -d "$TARGET" ];then check_names "$TARGET"||fail 'target symlink/special/unsafe names';oldkb=$(kb "$TARGET");fi
newkb=$(kb "portable/$SKIN");needw=$((oldkb+newkb+16384));needr=$((oldkb+16384))
[ $((used+needr)) -le 524288 ] || fail 'recovery quota would be exceeded'
if [ "$(stat -c %d "$BASE")" = "$(stat -c %d "$WBASE")" ];then [ "$(free_kb "$BASE")" -ge $((needw+needr)) ]||fail 'insufficient free storage';else [ "$(free_kb "$BASE")" -ge "$needr" ]&&[ "$(free_kb "$WBASE")" -ge "$needw" ]||fail 'insufficient recovery/work storage';fi
id="tx-$(date -u +%Y%m%dT%H%M%SZ)-$$";TX="$BASE/$id";WORK="$WBASE/$id";mkdir "$TX" "$WORK";chmod 700 "$TX" "$WORK"
printf '%s\n' ghost-installer-2 > "$TX/format";printf '%s\n' "$TX" > "$WORK/transaction"
for n in common.sh xml_contract.awk plugin_list.awk rollback.sh watchdog.sh recover.sh cleanup.sh control.sh;do cp "$n" "$TX/$n";done
for n in target settings service defer work global;do case "$n" in target)v=$TARGET;;settings)v=$SETTINGS;;service)v=$SERVICE;;defer)v=$DEFER;;work)v=$WORK;;global)v=$GLOBAL;;esac;printf '%s\n' "$v" > "$TX/$n";done
atomic "$GLOBAL/transaction" "$TX";owner > "$TX/worker";touch "$TX/context.ready"
cp -p "$SETTINGS" "$TX/settings.observed";awk -v report=registry -f xml_contract.awk "$TX/settings.observed"|LC_ALL=C sort > "$TX/registry.observed"
EXISTED=0;[ ! -d "$TARGET" ]||EXISTED=1;echo "$EXISTED" > "$TX/existed"
mkdir "$WORK/stage"
if [ "$EXISTED" = 1 ];then
 cp -a "$TARGET" "$TX/backup";inventory "$TARGET" > "$TX/files.before";verify_tree "$TX/backup" "$TX/files.before"||fail 'backup mismatch';cp -a "$TARGET/." "$WORK/stage/"
 OWN=legacy-owned.sha256;[ ! -f "$TARGET/.ghost-owned.sha256" ]||OWN="$TARGET/.ghost-owned.sha256";manifest_paths "$OWN"||fail 'invalid installed ownership'
 while IFS= read -r row;do h=${row%% *};p=${row#*  };[ ! -f "$WORK/stage/$p" ]||{ [ "$(hash "$WORK/stage/$p")" != "$h" ]||rm "$WORK/stage/$p"; };done < "$OWN"
fi
rm -f "$WORK/stage/.ghost-owned.sha256"
if [ "$ACTION" = install ];then
 while IFS= read -r row;do h=${row%% *};p=${row#*  };if [ -e "$WORK/stage/$p" ];then case "$p" in Presets/*|'Preset Library/'*|'Performance Presets/'*)continue;;*)fail "modified runtime collision: $p";;esac;fi;mkdir -p "$(dirname "$WORK/stage/$p")";cp -p "portable/$SKIN/$p" "$WORK/stage/$p";done < payload.sha256
 cp payload.sha256 "$WORK/stage/.ghost-owned.sha256"
fi
inventory "$WORK/stage" > "$TX/files.after"
# @HOOK staged
log "BACKUP VERIFIED: $TX; authoritative settings baseline pending host shutdown"
state prepared;sync;ARMED=1;touch "$TX/armed"
nohup sh "$TX/watchdog.sh" "$TX" </dev/null > "$TX/watchdog.log" 2>&1 & WATCH=$!
i=0;until [ -f "$TX/watchdog.ready" ];do kill -0 "$WATCH" || fail 'guardian exited';[ "$i" -lt 5 ]||fail 'guardian handshake';sleep 1;i=$((i+1));done
stop_host || fail 'host did not stop';state host-stopped
# Authoritative settings baseline begins ONLY after confirmed shutdown and a stable read.
cp -p "$SETTINGS" "$TX/settings.stable";sleep 1;cmp -s "$SETTINGS" "$TX/settings.stable"||fail 'settings not stable after stop'
awk -v report=registry -f xml_contract.awk "$TX/settings.stable"|LC_ALL=C sort > "$TX/registry.stopped"
cmp -s "$TX/registry.observed" "$TX/registry.stopped"||fail 'plugin registry changed during shutdown'
cp -p "$TX/settings.stable" "$TX/settings.before";touch "$TX/baseline.ready"
# @HOOK baseline
[ "$EXISTED" = 0 ]||verify_tree "$TARGET" "$TX/files.before"||fail 'concurrent plugin change'
sed "s|%payload-path%|$SYNTHS|g" "portable/$SKIN/plugin-meta.xml" > "$TX/entry"
MODE=add;[ "$ACTION" != uninstall ]||MODE=remove
awk -v mode="$MODE" -v file="$FILE" -v uid=47485354 -v entryfile="$TX/entry" -f plugin_list.awk "$TX/settings.before" > "$TX/settings.after"
awk -v report=registry -f xml_contract.awk "$TX/settings.after" > "$TX/registry.after"||fail 'invalid generated XML'
awk -v mode=remove -v file="$FILE" -v uid=47485354 -f plugin_list.awk "$TX/settings.before" > "$TX/foreign.before"
awk -v mode=remove -v file="$FILE" -v uid=47485354 -f plugin_list.awk "$TX/settings.after" > "$TX/foreign.after"
! grep -F "file=\"$TARGET/" "$TX/foreign.before" >/dev/null||fail 'foreign plugin inside GHOST'
cmp -s "$TX/foreign.before" "$TX/foreign.after"||fail 'foreign settings modified'
n=$(grep -c ' uid="47485354"' "$TX/registry.after"||true);if [ "$ACTION" = install ];then [ "$n" = 1 ];else [ "$n" = 0 ];fi||fail 'registration count'
# @HOOK registry
cmp -s "$SETTINGS" "$TX/settings.before"||fail 'concurrent settings edit'
state activating;touch "$TX/swap.intent"
[ "$EXISTED" = 0 ]||mv "$TARGET" "$WORK/original"
# @HOOK renamed
mv "$WORK/stage" "$TARGET";touch "$TX/activated"
# @HOOK activated
cp -p "$TX/settings.before" "$SETTINGS.ghost-new";cat "$TX/settings.after" > "$SETTINGS.ghost-new"
cmp -s "$SETTINGS" "$TX/settings.before"||fail 'concurrent registry write'
atomic "$TX/register.intent" yes
if ! cmp -s "$SETTINGS" "$TX/settings.after";then mv "$SETTINGS.ghost-new" "$SETTINGS";else rm "$SETTINGS.ghost-new";fi
touch "$TX/registered"
# @HOOK registered
verify_tree "$TARGET" "$TX/files.after"&&cmp -s "$SETTINGS" "$TX/settings.after"||fail 'post-activation verification'
state starting;start_host||fail 'host recovery failed'
# Host can legitimately save preferences on start; validate every registry entry remains identical.
awk -v report=registry -f xml_contract.awk "$SETTINGS"|LC_ALL=C sort > "$TX/registry.running"
LC_ALL=C sort "$TX/registry.after" > "$TX/registry.expected"
cmp -s "$TX/registry.running" "$TX/registry.expected"||fail 'registry differs after start'
verify_tree "$TARGET" "$TX/files.after"||fail 'files changed during start'
# @HOOK started
sync;touch "$TX/committed";state committed
if [ -d "$WORK/original" ];then verify_tree "$WORK/original" "$TX/files.before"||fail 'original copy changed; retained for review';remove_work_tree "$WORK/original";fi
log "COMMITTED: $TX; retention: max 3 transactions / 512 MiB; no automatic backup deletion"
