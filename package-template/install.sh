#!/bin/sh
set -eu
cd "$(dirname "$0")"
export GHOST_ACTION=install
exec sh transaction.sh "$@"
