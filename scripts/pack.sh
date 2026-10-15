#!/usr/bin/env bash
# Build the release files from plugins/.
#
# Format, confirmed against https://claude.com/docs/plugins/overview on 2026-10-13:
# Cowork and claude.ai accept "Add > Upload plugin" with a .zip or .plugin file. The archive may hold
# the plugin folder itself or its contents. It must hold exactly one .claude-plugin/plugin.json.
# Anthropic's own cowork-plugin-management skill builds the file with `zip -r name.plugin .` from
# inside the plugin folder, so this script zips the contents, with .claude-plugin/plugin.json at the root.
# Limits: 200 MB uncompressed, 5,000 files.
#
# Outputs:
#   dist/writing-<version>.plugin        the writing plugin, for Cowork and claude.ai upload
#   dist/dgonzo-plugins-<version>.zip    the whole marketplace, for `claude plugin marketplace add <folder>`
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
version="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$root/plugins/writing/.claude-plugin/plugin.json")"
dist="$root/dist"
mkdir -p "$dist"
rm -f "$dist/writing-$version.plugin" "$dist/dgonzo-plugins-$version.zip"

(cd "$root/plugins/writing" && zip -qr "$dist/writing-$version.plugin" . -x '*.DS_Store' -x '__pycache__/*' -x '*/__pycache__/*')
(cd "$root" && zip -qr "$dist/dgonzo-plugins-$version.zip" .claude-plugin plugins INSTALL.md CHANGELOG.md -x '*.DS_Store' -x '*/__pycache__/*')

echo "$dist/writing-$version.plugin"
echo "$dist/dgonzo-plugins-$version.zip"
