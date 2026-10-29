#!/bin/sh
# Read-only classification, shared by staging and the physical compatibility dry run.
set -eu
cd "$(dirname "$0")"
. ./common.sh
[ $# = 3 ] || fail 'usage: adoption.sh /existing/tree /Synths install|uninstall'
TREE=$1;SYNTHS=$2;ACTION=$3;SKIN='MPC-EURO - VST - GHOST'
safe_path "$TREE" && safe_path "$SYNTHS" || fail 'unsafe adoption paths'
case "$ACTION" in install|uninstall);;*)fail 'invalid adoption action';;esac
manifest_paths payload.sha256 && manifest_paths legacy-owned.sha256 || fail 'invalid adoption manifests'
if [ -e "$TREE" ];then
 [ -d "$TREE" ] && [ ! -L "$TREE" ] && check_names "$TREE" || fail 'unsafe adoption tree'
fi
if [ -e "$TREE/.ghost-owned.sha256" ];then
 [ -f "$TREE/.ghost-owned.sha256" ] || fail 'invalid ownership file type'
 # Never trust an arbitrary user-supplied manifest to claim unknown user files.
 cmp -s "$TREE/.ghost-owned.sha256" payload.sha256 || cmp -s "$TREE/.ghost-owned.sha256" legacy-owned.sha256 || fail 'unrecognised installed ownership manifest'
fi
expanded=$(sed "s|%payload-path%|$SYNTHS|g" "portable/$SKIN/plugin-meta.xml" | sha256sum - | cut -c 1-64)
awk 'NR==FNR{h[substr($0,67)]=$1;next}{p=substr($0,67);print $1 " " (p in h?h[p]:"-") " " p}' legacy-owned.sha256 payload.sha256 |
while IFS= read -r row;do
 new=${row%% *};rest=${row#* };old=${rest%% *};p=${rest#* }
 if [ ! -e "$TREE/$p" ];then
  if [ "$ACTION" = install ];then printf 'ADD\t%s\n' "$p";else printf 'ABSENT\t%s\n' "$p";fi
  continue
 fi
 [ -f "$TREE/$p" ] || fail "package file conflicts with directory: $p"
 case "$p" in Presets/*|'Preset Library/'*|'Performance Presets/'*|*.fxp|*.FXP)
  printf 'KEEP-PRESET\t%s\n' "$p";continue;;esac
 current=$(hash "$TREE/$p")
 if [ "$current" != "$new" ] && [ "$current" != "$old" ];then
  [ "$p" = plugin-meta.xml ] && [ "$current" = "$expanded" ] || fail "modified runtime collision: $p"
 fi
 printf 'REMOVE-OWNED\t%s\n' "$p"
done
