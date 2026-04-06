#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec /usr/bin/python3 "$SCRIPT_DIR/scripts/uninstall_personal_plugin.py"
