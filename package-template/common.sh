#!/bin/sh
# POSIX/BusyBox shared safety primitives. No production test-mode bypasses.
set -eu
fail() { echo "REFUSED: $*" >&2; exit 1; }
log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
atomic() { printf '%s\n' "$2" > "$1.tmp.$$"; mv "$1.tmp.$$" "$1"; }
hash() { sha256sum "$1" | cut -c 1-64; }
proc_id() { [ -r "/proc/$1/stat" ] || return 1; sed 's/.*) //' "/proc/$1/stat" | awk 'NF>=20 {print $20}'; }
boot() { cat /proc/sys/kernel/random/boot_id; }
owner() { printf '%s %s %s\n' "$$" "$(proc_id $$)" "$(boot)"; }
alive() {
 # Conservative on unreadable/corrupt ownership: unknown is busy, never proof of death.
 read -r p s b < "$1" || return 0
 case "$p:$s" in *[!0-9:]*|:|*:) return 0;;esac
 currentboot=$(boot 2>/dev/null) || return 0
 [ -n "$currentboot" ] || return 0
 [ "$b" = "$currentboot" ] || return 1
 actual=$(proc_id "$p" 2>/dev/null || true)
 if [ -n "$actual" ];then [ "$actual" = "$s" ];return;fi
 if kill -0 "$p" 2>/dev/null || [ -d "/proc/$p" ];then return 0;fi
 return 1
}
matches() {
 read -r p s b < "$1" || return 1
 case "$p:$s" in *[!0-9:]*|:|*:)return 1;;esac
 [ "$b" = "$(boot)" ] && [ -n "$s" ] && [ "$(proc_id "$p" 2>/dev/null || true)" = "$s" ] && kill -0 "$p" 2>/dev/null
}
cancel_control() {
 [ -f "$TX/control.owner" ] || return 0
 if alive "$TX/control.owner";then
  matches "$TX/control.owner" || return 1
  controlpid=$(awk '{print $1}' "$TX/control.owner");kill -TERM "$controlpid" 2>/dev/null||true
  j=0;while alive "$TX/control.owner";do
   [ "$j" -lt 5 ]||break;sleep 1;j=$((j+1))
  done
  if alive "$TX/control.owner";then matches "$TX/control.owner"||return 1;kill -KILL "$controlpid" 2>/dev/null||true;fi
 fi
 rm -f "$TX/control.owner"
}

safe_path() {
 printf '%s' "$1" | LC_ALL=C grep -q '[[:cntrl:]]' && return 1
 [ "$1" != / ] || return 1
 case "$1" in /*) ;; *) return 1;;esac; case "$1" in *'..'*|*'//'*|*'\'*|*'|'*|*'&'*|*'"'*|*"'"*|*'<'*|*'>'*) return 1;;esac; }
canon() { [ -d "$1" ] || return 1; (cd "$1" && pwd -P); }
no_special() { special=$(find "$1" ! -type d ! -type f -print) || return 1; [ -z "$special" ]; }
inventory() { (cd "$1"; find . -type f | LC_ALL=C sort | while IFS= read -r p;do sha256sum "$p" || exit;done); }
verify_tree() { inventory "$1" > "$TX/check.$$"; cmp -s "$TX/check.$$" "$2"; }
manifest_paths() { awk 'length($1)!=64 || $1~/[^0-9a-f]/ {exit 1} {p=substr($0,67); if(substr($0,65,2)!="  " || p=="" || p~/^\// || p~/(^|\/)\.\.?($|\/)/ || p~/\\/ || p~/[\t\r]/ || seen[p]++) exit 1} END {if(NR==0)exit 1}' "$1"; }
# Refuse unsupported names/special files before any recursive copy.
check_names() {
 bad=$(find "$1" -exec sh -c 'for p do case "$p" in *"
"*|*"	"*|*"
"*|*"\\"*) printf bad;;esac;done' sh {} +) || return 1
 [ -z "$bad" ] && no_special "$1"
}
read_context() {
 TX=$(canon "$1") || fail 'transaction missing'
 [ -f "$TX/format" ] && [ "$(cat "$TX/format")" = ghost-installer-2 ] || fail 'unknown transaction'
 TARGET=$(cat "$TX/target"); SETTINGS=$(cat "$TX/settings"); SERVICE=$(cat "$TX/service"); DEFER=$(cat "$TX/defer"); WORK=$(cat "$TX/work"); GLOBAL=$(cat "$TX/global")
 safe_path "$TARGET" && safe_path "$SETTINGS" && safe_path "$WORK" || fail 'unsafe saved context'
 [ "$(cat "$WORK/transaction")" = "$TX" ] || fail 'work ownership mismatch'
}
# Only these explicitly recorded, installer-created trees may be removed.
remove_work_tree() { case "$1" in "$WORK/stage"|"$WORK/original"|"$WORK/restore"|"$WORK/failed") ;; *) fail 'cleanup scope';;esac; [ ! -L "$1" ] || fail 'symbolic cleanup'; rm -rf "$1"; }
state() { atomic "$TX/state" "$1"; log "$1"; }
service_cmd() {
 op=$1;grant=$(mktemp "$TX/control.grant.XXXXXX");rm "$grant";parent=$(mktemp "$TX/control.parent.XXXXXX");owner > "$parent"
 sh "$TX/control.sh" "$TX" "$op" "$grant" "$parent" & c=$!;ci=$(proc_id "$c" 2>/dev/null || true);i=0
 if [ -n "$ci" ];then atomic "$TX/control.owner" "$c $ci $(boot)";touch "$grant";fi
 while kill -0 "$c" 2>/dev/null;do
  [ -n "$ci" ] || return 1
  [ "$i" -lt 30 ] || { cancel_control || return 1;wait "$c" || true;return 1; }
  sleep 1;i=$((i+1))
 done
 wait "$c";rc=$?;rm -f "$TX/control.owner" "$grant" "$parent";return "$rc"
}
stop_host() {
 [ "$DEFER" = 0 ] || { ! pidof MPC >/dev/null || return 1; return; }
 service_cmd stop || return 1
 i=0;while pidof MPC >/dev/null;do [ "$i" -lt 60 ] || return 1;sleep 1;i=$((i+1));done
 ! systemctl is-active --quiet "$SERVICE"
}
content_roots_now() { (
 CONTENT=$(mktemp) || exit 1;trap 'rm -f "$CONTENT"' EXIT
 LC_ALL=C awk -v report=locations -f "$TX/xml_contract.awk" "$SETTINGS" > "$CONTENT" || exit 1
 [ -s "$CONTENT" ] || exit 1
 printf '%s\n' "$(dirname "$TARGET")" >> "$CONTENT"
 outside_content "$TX" && outside_content "$WORK"
); }
start_host() {
 content_roots_now || { log 'Current discovery paths overlap recovery/work or XML is unsupported';return 1; }
 [ "$DEFER" = 0 ] || return 0
 service_cmd start || return 1
 i=0;until systemctl is-active --quiet "$SERVICE" && pidof MPC >/dev/null;do [ "$i" -lt 60 ] || return 1;sleep 1;i=$((i+1));done
 p=$(systemctl show -p MainPID --value "$SERVICE"); n=$(systemctl show -p NRestarts --value "$SERVICE")
 [ "$p" != 0 ] || return 1;sleep 2
 [ "$p" = "$(systemctl show -p MainPID --value "$SERVICE")" ] && [ "$n" = "$(systemctl show -p NRestarts --value "$SERVICE")" ] && systemctl is-active --quiet "$SERVICE"
}
# Stale ownership is never inferred from PID alone. Atomic takeover of a dead lease.
lease() {
 lock=$1;i=0
 while ! mkdir "$lock" 2>/dev/null;do
  [ ! -f "$TX/rollback.done" ] || return 2
  if [ -f "$lock/owner" ] && ! alive "$lock/owner";then
   sig=$(hash "$lock/owner" 2>/dev/null || true);node=$(stat -c %d:%i "$lock" 2>/dev/null || true)
   if mkdir "$lock/takeover" 2>/dev/null;then
    if alive "$lock/owner" || [ "$(hash "$lock/owner" 2>/dev/null || true)" != "$sig" ] || [ "$(stat -c %d:%i "$lock" 2>/dev/null || true)" != "$node" ];then rmdir "$lock/takeover";continue;fi
    # Nobody can acquire this same lease until the old directory is renamed.
    mv "$lock" "$lock.dead.$$" || return 1
    continue
   fi
  fi
  [ "$i" -lt 300 ] || return 1;sleep 1;i=$((i+1))
 done
 owner > "$lock/owner.tmp.$$";mv "$lock/owner.tmp.$$" "$lock/owner";return 0
}
release_global() {
 [ -d "$GLOBAL" ] || return 0
 [ -f "$GLOBAL/transaction" ] && [ "$(cat "$GLOBAL/transaction")" = "$TX" ] || return 1
 # TX lock serializes release against stale transaction recovery.
 rm -f "$GLOBAL/owner" "$GLOBAL/transaction";rmdir "$GLOBAL"
}
# Resolve existing/nonexistent content paths without trusting a lexical alias.
resolve_path() {
 p=$1;tail=''
 while [ ! -d "$p" ];do [ "$p" != / ] || return 1;tail="/$(basename "$p")$tail";p=$(dirname "$p");done
 printf '%s%s\n' "$(canon "$p")" "$tail"
}
outside_content() {
 root=$1
 while IFS= read -r loc;do
  [ -n "$loc" ] || continue
  safe_path "$loc" || { log "Unsupported discovery path encoding or unsafe characters" >&2;return 1; }
  c=$(resolve_path "$loc") || return 1
  case "$root/" in "$c/"*) log "Recovery/work root is within a discovery path" >&2;return 1;;esac
  case "$c/" in "$root/"*) log "Discovery path is within a recovery/work root" >&2;return 1;;esac
 done < "$CONTENT"
}
mount_options() {
 p=$1;awk -v p="$p" 'function dec(s){gsub(/\\040/," ",s);gsub(/\\011/,"\t",s);return s} {m=dec($2);if(m=="/" || p==m || index(p,m"/")==1){if(length(m)>best){best=length(m);o=$4}}}END{if(!best)exit 1;print o}' /proc/mounts
}
mount_check() { o=$(mount_options "$1") || return 1;case ",$o," in *,ro,*) return 1;;esac;if [ "$2" = exec ];then case ",$o," in *,noexec,*)return 1;;esac;fi; }
free_kb() { df -Pk "$1" | awk 'NR==2 {print $4}'; }
kb() { du -sk "$1" | awk '{print $1}'; }
# Registry conflicts must refuse before stop; do not silently replace another UID owner.
registry_scope() {
 printf '%s\n' "$1" | awk -v file="$FILE" -v dir="$TARGET/" '
 index($0," uid=\"47485354\"") {n++;if(!index($0," file=\"" file "\""))bad=1}
 !index($0," uid=\"47485354\"") && index($0," file=\"" dir) {bad=1}
 END {exit (bad || n>1)}'
}
