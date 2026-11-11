#!/usr/bin/env bash
# Warhammer syntax, standalone build, and local tests. No deploy and no production probe.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m compileall -q \
  tools/build_standalone_wh.py \
  tools/build_wh_codex.py \
  tools/make_favicon_wh.py \
  tools/smoke_warhammer.py \
  tools/probe_live.py \
  tools/ci_paths.py

find extra_sites/warhammer-survivors -name '*.js' -print0 | xargs -0 -n1 node --check
node --check tools/smoke_dom.mjs
node --check tools/smoke_codex.mjs

python3 tools/ci_paths.py --self-test
python3 tools/build_standalone_wh.py
python3 tools/build_standalone_wh.py --check
python3 tools/smoke_warhammer.py
python3 tools/smoke_warhammer.py --self-test
node tools/smoke_codex.mjs
python3 tools/probe_live.py --self-test
