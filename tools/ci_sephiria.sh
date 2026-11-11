#!/usr/bin/env bash
# Sephiria syntax, build, and local tests. No deploy and no production probe.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m compileall -q \
  build.py \
  tools/check_seo_consistency.py \
  tools/check_village.py \
  tools/check_guide_visuals.py \
  tools/swap_test.py \
  tools/smoke_sephiria.py \
  tools/probe_live.py \
  tools/ci_paths.py \
  tools/make_favicon.py \
  tools/make_svg_figures.py \
  tools/export_content.py

find assets functions -name '*.js' -print0 | xargs -0 -n1 node --check
node --check tools/smoke_dom.mjs
node --check tools/smoke_login.mjs

python3 tools/ci_paths.py --self-test
python3 build.py
python3 tools/check_seo_consistency.py
python3 tools/swap_test.py
python3 tools/check_village.py
python3 tools/check_guide_visuals.py
python3 tools/smoke_sephiria.py
python3 tools/smoke_sephiria.py --self-test
node tools/smoke_login.mjs
python3 tools/probe_live.py --self-test
