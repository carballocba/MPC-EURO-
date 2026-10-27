#!/bin/sh
set -eu
cd "$(dirname "$0")"
export GHOST_ACTION=uninstall
exec sh transaction.sh "$@"
