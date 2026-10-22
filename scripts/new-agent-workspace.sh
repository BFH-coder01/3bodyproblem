#!/usr/bin/env sh
# Pass the normal workspaces.py arguments, starting with plan or create.
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$script_dir/workspaces.py" "$@"
