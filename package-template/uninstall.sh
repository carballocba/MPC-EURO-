#!/bin/sh
set -eu
# -n leaves host stop/start ownership with the batch caller.
DEFER=0
export DEFER
cd "$(dirname "$0")"
export GHOST_ACTION=uninstall
exec sh transaction.sh "$@"
