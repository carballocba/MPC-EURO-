#!/bin/sh
# GPL-3.0-only; GHOST-only durable transaction. No remote Python/base64/timeout.
set -u
export LC_ALL=C
ACTION=${ACTION:-run};TX=${TX:?TX required}
[ -d "$TX" ] && [ ! -L "$TX" ] || exit 2
. "$TX/plan.conf"
# All values are generated/quoted by manage.py from a locally parsed XML snapshot.
[ "$TARGET" = "$SYNTHS/MPC-EURO - VST - GHOST" ] || exit 2
case "$TX" in "$SYNTHS"/.ghost-recovery/tx-*) ;; *) exit 2;; esac
LOCK="$SYNTHS/.ghost-community-lock";MUTATING=0;OWNED=0;STEP=preflight;guardian=''
hash(){ sha256sum "$1" | sed 's/[[:space:]].*//'; }
attr(){ systemctl show "$SERVICE" "-p$1" | sed 's/^[^=]*=//'; }
active(){ [ "$(attr ActiveState)" = active ] && [ "$(attr SubState)" = running ] && [ "$(attr MainPID)" -gt 1 ]; }
verify(){
 [ -d "$1" ] && [ ! -L "$1" ] || return 1
 [ -z "$(find "$1" ! -type f ! -type d -print)" ] || return 1
 [ "$(find "$1" -type f | wc -l)" -eq "$(wc -l < "$2")" ] || return 1
 (cd "$1" && sha256sum -c "$2") >/dev/null 2>&1
}
protected(){
 if [ -s "$TX/protected.sha256" ];then (cd / && sha256sum -c "$TX/protected.sha256") >/dev/null 2>&1 || return 1;fi
 while IFS= read -r p;do [ ! -e "$p" ] || return 1;done < "$TX/protected.missing"
}
stop(){
 systemctl --no-block stop "$SERVICE" || return 1
 i=0;while [ "$i" -lt 30 ];do [ "$(attr ActiveState)" != inactive ] || { [ "$(attr MainPID)" != 0 ] || return 0; };sleep 1;i=$((i+1));done;return 1
}
start(){
 systemctl --no-block start "$SERVICE" || return 1
 i=0;while [ "$i" -lt 30 ];do active && break;sleep 1;i=$((i+1));done
 active || return 1
 p=$(attr MainPID);n=$(attr NRestarts);sleep "$OBSERVE_SECONDS"
 active && [ "$(attr MainPID)" = "$p" ] && [ "$(attr NRestarts)" = "$n" ]
}
identity(){
 if [ "${GHOST_FIXTURE:-0}" = 1 ];then kill -0 "$1" 2>/dev/null && echo "fixture-$1";return;fi
 line=$(cat "/proc/$1/stat" 2>/dev/null) || return 1
 rest=${line##*) };set -- $rest;j=1;while [ "$j" -lt 20 ];do shift;j=$((j+1));done;echo "$1"
}
alive(){ [ "$(identity "$1" 2>/dev/null || :)" = "$2" ] && [ -n "$2" ]; }
release(){
 [ -f "$LOCK/owner" ] && [ "$(cat "$LOCK/owner")" = "$TX" ] || return 0
 rm -f "$LOCK/owner";rmdir "$LOCK"
}
acquire(){
 if ! mkdir "$LOCK" 2>/dev/null;then
  [ "$ACTION" = rollback ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$TX" ] || return 1
  oldworker=$(cat "$TX/worker.pid" 2>/dev/null || :);oldstart=$(cat "$TX/worker.start" 2>/dev/null || :)
  oldguard=$(cat "$TX/guardian.pid" 2>/dev/null || :);oldgstart=$(cat "$TX/guardian.start" 2>/dev/null || :)
  alive "$oldworker" "$oldstart" && return 1
  alive "$oldguard" "$oldgstart" && return 1
  release;mkdir "$LOCK" || return 1
 fi
 printf '%s\n' "$TX" > "$LOCK/owner";OWNED=1; }
registry_restore(){
 current=$(hash "$SETTINGS") || return 1
 [ "$current" != "$BEFORE_SHA" ] || return 0
 next="$SETTINGS.ghost-recovery-$$"
 cp -p "$SETTINGS" "$next" || return 1
 if [ "$current" = "$AFTER_SHA" ];then cat "$TX/settings.before" > "$next" || return 1
 else
  # Preserve concurrent preference/foreign-plugin edits. Replace only our exact token.
  awk -v oldfile="$TX/registry.after.token" -v newfile="$TX/registry.before.token" -v oldlen="$AFTER_TOKEN_LEN" -v newlen="$BEFORE_TOKEN_LEN" -f "$TX/registry_inverse.awk" "$SETTINGS" > "$next" || { rm -f "$next";return 1; }
  : > "$TX/concurrent-settings-preserved"
 fi
 [ "$(hash "$SETTINGS")" = "$current" ] || { rm -f "$next";return 1; }
 mv -f "$next" "$SETTINGS"
}
restore(){
 [ "$(hash "$TX/settings.before")" = "$BEFORE_SHA" ] || return 1
 [ "$OLD_EXISTS" = 0 ] || verify "$TX/backup" "$TX/current.sha256" || verify "$TX/prior-active" "$TX/current.sha256" || return 1
 stop || return 1
 if [ "$OLD_EXISTS" = 1 ];then
  if ! verify "$TARGET" "$TX/current.sha256";then
   if verify "$TX/prior-active" "$TX/current.sha256";then restore="$TX/prior-active"
   else
    restore="$TX/restore-$$";[ ! -e "$restore" ] || return 1
    cp -Rp "$TX/backup" "$restore" && verify "$restore" "$TX/current.sha256" || return 1
   fi
   if [ -e "$TARGET" ];then
    slot=0;while [ -e "$TX/rejected-$slot" ];do slot=$((slot+1));done
    mv "$TARGET" "$TX/rejected-$slot" || return 1
   fi
   mv "$restore" "$TARGET" || return 1
  fi
 else
  if [ -e "$TARGET" ];then
   slot=0;while [ -e "$TX/rejected-$slot" ];do slot=$((slot+1));done
   mv "$TARGET" "$TX/rejected-$slot" || return 1
  fi
 fi
 registry_ok=1;registry_restore || registry_ok=0
 sync
 # Restore the host even when an unrelated concurrent registry change requires review.
 start || { : > "$TX/host-recovery-failed";return 1; }
 [ "$registry_ok" = 1 ] || { : > "$TX/registry-review-required";return 1; }
 [ "$OLD_EXISTS" = 0 ] || verify "$TARGET" "$TX/current.sha256" || return 1
 : > "$TX/rollback-complete";: > "$TX/done"
 protected || { : > "$TX/foreign-change-preserved-review";return 1; }
 echo 'GHOST rollback complete; current foreign state preserved'
}
finish(){
 code=$?
 trap - EXIT HUP INT TERM
 if [ "$code" != 0 ] && [ "$MUTATING" = 1 ] && [ ! -f "$TX/done" ];then
  echo "FAILED: $STEP; restoring GHOST" >&2
  restore > "$TX/recovery.log" 2>&1 || { code=90;echo "RECOVERY NEEDS REVIEW: $TX" >&2; }
 fi
 if [ "$MUTATING" = 0 ] || [ -f "$TX/done" ];then
  : > "$TX/done"
  # Reap our guardian before allowing a new operation on this same transaction.
  [ -z "$guardian" ] || wait "$guardian" 2>/dev/null || :
  release
 fi
 printf 'exit=%s operation=%s\n' "$code" "$STEP" > "$TX/result.txt"
 exit "$code"
}
arm(){
 [ ! -f "$TX/done" ] || mv "$TX/done" "$TX/previous-done-$$"
 rm -f "$TX/guardian-ready"
 echo "$$" > "$TX/worker.pid";identity "$$" > "$TX/worker.start" || return 1
 nohup env ACTION=guardian TX="$TX" sh "$TX/transaction.sh" > "$TX/watchdog.log" 2>&1 < /dev/null &
 guardian=$!;echo "$guardian" > "$TX/guardian.pid";identity "$guardian" > "$TX/guardian.start" || return 1;i=0
 while [ "$i" -lt 10 ];do kill -0 "$guardian" 2>/dev/null || return 1;[ ! -f "$TX/guardian-ready" ] || return 0;sleep 1;i=$((i+1));done;return 1
}
fault(){
 [ "${GHOST_FIXTURE:-0}" = 1 ] || return 0
 [ "${GHOST_FAIL_AT:-}" != "$1" ] || exit 71
 [ "${GHOST_FAIL_AT:-}" != "kill-$1" ] || kill -KILL "$$"
 [ "${GHOST_FAIL_AT:-}" != "hang-$1" ] || { while :;do sleep 1;done; }
}
for tool in sh systemctl sha256sum sed find wc cp mv mkdir rmdir rm sleep kill nohup env sync cat awk chmod;do command -v "$tool" >/dev/null || exit 2;done
if [ "${GHOST_FIXTURE:-0}" != 1 ];then
 [ "$(id -u)" = 0 ] || exit 2
 case "$(uname -m)" in armv7*) ;; *) echo 'Gen1 ARMv7 only' >&2;exit 2;; esac
 [ "${GHOST_FAIL_AT:-}" = '' ] || exit 2
fi
if [ "$ACTION" = guardian ];then
 : > "$TX/guardian-ready";worker=$(cat "$TX/worker.pid");expected=$(cat "$TX/worker.start");n=0
 while [ "$n" -lt "$GUARD_SECONDS" ];do
  [ ! -f "$TX/done" ] || exit 0
  alive "$worker" "$expected" || break
  sleep 1;n=$((n+1))
 done
 [ ! -f "$TX/done" ] || exit 0
 if alive "$worker" "$expected";then
  kill -TERM "$worker" 2>/dev/null || :;sleep "$GUARD_GRACE"
  [ ! -f "$TX/done" ] || exit 0
  alive "$worker" "$expected" && kill -KILL "$worker" 2>/dev/null || :
  # Wait until the exact worker has died before independent takeover.
  i=0;while alive "$worker" "$expected" && [ "$i" -lt 10 ];do sleep 1;i=$((i+1));done
  alive "$worker" "$expected" && exit 90
 fi
 [ ! -f "$TX/armed" ] || { restore > "$TX/watchdog-recovery.log" 2>&1 || exit 90; }
 : > "$TX/done";release;exit 0
fi
acquire || { echo 'Another GHOST transaction/recovery holds the lock' >&2;exit 2; }
trap finish EXIT;trap 'exit 130' HUP INT TERM
if [ "$ACTION" = rollback ];then
 # Backups are never deleted; an already-restored exact state needs no service restart.
 if [ "$(hash "$SETTINGS")" = "$BEFORE_SHA" ] && active && protected;then
  baseline_ok=0
  if [ "$OLD_EXISTS" = 1 ];then verify "$TARGET" "$TX/current.sha256" && baseline_ok=1
  else [ -e "$TARGET" ] || baseline_ok=1;fi
  if [ "$baseline_ok" = 1 ];then : > "$TX/rollback-complete";echo 'IDEMPOTENT: baseline already active';exit 0;fi
 fi
 arm || exit 2;MUTATING=1;: > "$TX/armed";STEP=explicit-rollback;restore || exit 1;MUTATING=0;exit 0
fi
[ "$ACTION" = run ] && [ ! -f "$TX/committed" ] && [ ! -f "$TX/backup-ready" ] || exit 2
STEP=verify-fresh-baseline
active && [ "$(attr MainPID)" = "$EXPECT_PID" ] && [ "$(attr NRestarts)" = "$EXPECT_RESTARTS" ] || exit 2
[ "$(hash "$SETTINGS")" = "$BEFORE_SHA" ] && protected || exit 2
[ "$(hash "$TX/settings.after")" = "$AFTER_SHA" ] || exit 2
if [ "$OLD_EXISTS" = 1 ];then
 verify "$TARGET" "$TX/current.sha256" || exit 2
 cp -Rp "$TARGET" "$TX/backup" && verify "$TX/backup" "$TX/current.sha256" || exit 2
else [ ! -e "$TARGET" ] || exit 2;fi
[ "$OP" != install ] || verify "$TX/candidate" "$TX/candidate.sha256" || exit 2
[ "$(hash "$TX/settings.before")" = "$BEFORE_SHA" ] || exit 2
: > "$TX/backup-ready";arm || exit 2
STEP=final-gate
[ "$(hash "$SETTINGS")" = "$BEFORE_SHA" ] && protected && active && [ "$(attr MainPID)" = "$EXPECT_PID" ] && [ "$(attr NRestarts)" = "$EXPECT_RESTARTS" ] || exit 2
STEP=stop;MUTATING=1;: > "$TX/armed";sync;stop || exit 1;fault after-stop
[ "$(hash "$SETTINGS")" = "$BEFORE_SHA" ] || exit 1
STEP=preserve-old;[ ! -e "$TARGET" ] || mv "$TARGET" "$TX/prior-active" || exit 1;fault after-old-moved
STEP=activate;[ "$OP" != install ] || { mv "$TX/candidate" "$TARGET" && verify "$TARGET" "$TX/candidate.sha256"; } || exit 1;fault after-activation
STEP=registry
if [ "$BEFORE_SHA" != "$AFTER_SHA" ];then
 [ "$(hash "$SETTINGS")" = "$BEFORE_SHA" ] || exit 1
 cp -p "$SETTINGS" "$SETTINGS.ghost-next-$$" && cat "$TX/settings.after" > "$SETTINGS.ghost-next-$$" && mv -f "$SETTINGS.ghost-next-$$" "$SETTINGS" || exit 1
fi
fault after-registry
STEP=start;sync;start && protected || exit 1;fault after-start
[ "$(hash "$SETTINGS")" = "$AFTER_SHA" ] || exit 1
[ "$OP" != install ] || verify "$TARGET" "$TX/candidate.sha256" || exit 1
[ "$OP" != uninstall ] || [ ! -e "$TARGET" ] || exit 1
: > "$TX/committed";: > "$TX/done";MUTATING=0;echo 'FILES/REGISTRY/HOST VERIFIED; hardware audio/GUI untested';exit 0
