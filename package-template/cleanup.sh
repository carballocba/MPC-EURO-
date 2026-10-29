#!/bin/sh
# Explicit export-before-cleanup, never automatic deletion and never on Synths.
set -eu
cd "$(dirname "$0")";. ./common.sh
[ $# = 4 ]&&[ "$2" = --export ]&&[ "$4" = --confirm ]||fail 'usage: cleanup.sh /exact/tx --export /new/independent-folder --confirm'
read_context "$1";EXPORT=$3
safe_path "$EXPORT"&&[ ! -e "$EXPORT" ]||fail 'export path must be new/absolute'
case "$EXPORT/" in "$TX/"*|"$WORK/"*)fail 'export overlaps transaction';;esac
[ -f "$TX/committed" ]||[ -f "$TX/rollback.done" ]||fail 'incomplete recovery cannot be cleaned'
[ ! -e "$GLOBAL" ]||fail 'active or interrupted transaction must be resolved first'
# Keep newest recoverable state on this device. Older complete records only.
BASE=$(dirname "$TX");latest=$(for t in "$BASE"/tx-*;do
 [ -d "$t" ] && [ -f "$t/format" ] && [ "$(cat "$t/format")" = ghost-installer-2 ] || continue
 if [ -f "$t/committed" ] || [ -f "$t/rollback.done" ];then printf '%s\n' "$t";fi
done | LC_ALL=C sort | tail -n 1)
[ "$latest" != "$TX" ]||fail 'cannot remove newest recovery point'
CONTENT=$(mktemp);trap 'rm -f "$CONTENT"' EXIT
LC_ALL=C awk -v report=locations -f "$TX/xml_contract.awk" "$SETTINGS" > "$CONTENT" || fail 'content roots unavailable'
printf '%s\n' "$(dirname "$TARGET")" >> "$CONTENT"
outside_content "$(resolve_path "$EXPORT")" || fail 'export overlaps content discovery'
check_names "$TX" && check_names "$WORK" || fail 'export contains unsupported files'
mkdir "$EXPORT";chmod 700 "$EXPORT";cp -a "$TX" "$EXPORT/transaction";cp -a "$WORK" "$EXPORT/work"
inventory "$TX" > "$EXPORT/original.sha256";inventory "$EXPORT/transaction" > "$EXPORT/copied.sha256";cmp -s "$EXPORT/original.sha256" "$EXPORT/copied.sha256"||fail 'transaction export mismatch'
inventory "$WORK" > "$EXPORT/work.original.sha256";inventory "$EXPORT/work" > "$EXPORT/work.copied.sha256";cmp -s "$EXPORT/work.original.sha256" "$EXPORT/work.copied.sha256"||fail 'work export mismatch'
sync
# Paths are exact self-owned namespaces, never a wildcard or a content/Synths root.
[ "$(cat "$WORK/transaction")" = "$TX" ]&&[ "$(cat "$TX/format")" = ghost-installer-2 ]||fail 'ownership changed'
rm -rf "$WORK" "$TX"
log "Older completed transaction exported and cleaned: $EXPORT; newest retained"
