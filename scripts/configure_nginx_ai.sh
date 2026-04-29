#!/usr/bin/env bash
# Copyright 2026 Jiacheng Ni
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail

SERVER_NAME="${YOLOONG_NGINX_SERVER_NAME:-www.yoloong.com}"
UPSTREAM="${YOLOONG_NGINX_UPSTREAM:-http://127.0.0.1:8721}"
SNIPPET_PATH="${YOLOONG_NGINX_SNIPPET:-/etc/nginx/snippets/yoloong-ai-location.conf}"
BACKUP_ROOT="${BACKUP_ROOT:-/root/yoloong-ai-backups}"
RESTORE_MANIFEST="/tmp/yoloong-ai-nginx-restore"

if ! command -v nginx >/dev/null 2>&1; then
  echo "nginx is not installed; skipping /ai/ proxy configuration." >&2
  exit 0
fi

mkdir -p "$(dirname "$SNIPPET_PATH")" "$BACKUP_ROOT"
rm -f "$RESTORE_MANIFEST"

cat > "$SNIPPET_PATH" <<EOF
# Managed by Yoloong-AI. Do not put secrets in this file.
location = /ai {
    return 302 /ai/;
}

location /ai/ {
    proxy_pass $UPSTREAM;
    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_set_header X-Forwarded-Prefix /ai;
    proxy_read_timeout 300s;
}
EOF

python3 - "$SERVER_NAME" "$SNIPPET_PATH" "$BACKUP_ROOT" "$RESTORE_MANIFEST" <<'PY'
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

server_name = sys.argv[1]
snippet_path = sys.argv[2]
backup_root = Path(sys.argv[3])
restore_manifest = Path(sys.argv[4])
include_line = f"    include {snippet_path};"
search_roots = [
    Path("/etc/nginx/conf.d"),
    Path("/etc/nginx/sites-available"),
    Path("/etc/nginx/sites-enabled"),
]


def find_matching_blocks(text: str) -> list[tuple[int, int]]:
    blocks: list[tuple[int, int]] = []
    cursor = 0
    while True:
        start = text.find("server", cursor)
        if start == -1:
            return blocks
        brace = text.find("{", start)
        if brace == -1:
            return blocks
        if text[start:brace].strip() != "server":
            cursor = start + len("server")
            continue
        depth = 0
        for index in range(brace, len(text)):
            char = text[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    block = text[start : index + 1]
                    if "server_name" in block and server_name in block:
                        blocks.append((start, index + 1))
                    cursor = index + 1
                    break
        else:
            return blocks


targets: list[tuple[Path, list[tuple[int, int]]]] = []
seen_files: set[Path] = set()
for root in search_roots:
    if not root.exists():
        continue
    for candidate in sorted(root.glob("*.conf")):
        real_candidate = candidate.resolve()
        if real_candidate in seen_files:
            continue
        seen_files.add(real_candidate)
        text = candidate.read_text(encoding="utf-8", errors="replace")
        blocks = find_matching_blocks(text)
        if blocks:
            targets.append((candidate, blocks))

if not targets:
    raise SystemExit(f"Could not find nginx server block for {server_name}.")

timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
manifest_lines: list[str] = []

for target_file, blocks in targets:
    text = target_file.read_text(encoding="utf-8", errors="replace")
    updated = text
    changed = False
    for start, end in reversed(blocks):
        block = updated[start:end]
        if include_line.strip() in block:
            continue
        insert_at = updated.rfind("}", start, end)
        if insert_at == -1:
            raise SystemExit(f"Could not locate closing brace in {target_file}.")
        updated = updated[:insert_at].rstrip() + "\n\n" + include_line + "\n" + updated[insert_at:]
        changed = True
    if not changed:
        print(f"nginx /ai/ include already present in {target_file}")
        continue

    backup = backup_root / f"{target_file.name}.{timestamp}.bak"
    shutil.copy2(target_file, backup)
    manifest_lines.extend([str(target_file), str(backup)])
    target_file.write_text(updated, encoding="utf-8")
    print(f"Inserted /ai/ include into {target_file}; backup: {backup}")

if manifest_lines:
    restore_manifest.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
PY

if ! nginx -t; then
  if [ -f "$RESTORE_MANIFEST" ]; then
    while IFS= read -r target && IFS= read -r backup; do
      cp "$backup" "$target"
      echo "nginx -t failed; restored $target from $backup." >&2
    done < "$RESTORE_MANIFEST"
  fi
  exit 1
fi

systemctl reload nginx || nginx -s reload
rm -f "$RESTORE_MANIFEST"
echo "nginx /ai/ proxy configured for $SERVER_NAME -> $UPSTREAM"
