#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path.cwd()

def replace_once(path, old, new):
    p = ROOT / path
    data = p.read_text(encoding="utf-8")
    count = data.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected exactly 1 match, found {count}")
    p.write_text(data.replace(old, new, 1), encoding="utf-8")

# -------------------------------------------------------------------------
# 0.9.4 — surgical fixes on top of the exact 0.8.19 source stack.
# 1) First Home paint: seed the EXISTING thumbnail-quality verifier from the
#    thumbnails already rendered before the JSON hook saw them.
# 2) First-video audio: remove ONLY the custom SourceBuffer buffer limiter.
#
# No menu/sidebar, icon, Recents, layout, adblock, codec, player UI or visual
# rule is changed.
# -------------------------------------------------------------------------

# AUDIO FIX: stop intercepting MediaSource/SourceBuffer.
remove_import = "import { initBufferLimit } from './hooks/buffer-limit.js';\nimport { getWebOSVersion } from './webos-utils.js';\n"
if (ROOT / "src/userScript.js").read_text(encoding="utf-8").count(remove_import) != 1:
    raise RuntimeError("userScript.js: buffer-limit imports not found exactly once")
replace_once("src/userScript.js", remove_import, "")

old_buffer = """if (typeof initBufferLimit === 'function' && getWebOSVersion() <= 4) {
\tinitBufferLimit({ retainBehindSecs: 20, minTrimSecs: 10, trimIntervalMs: 5000 });
\tconsole.info('Initiating UK6530 Lite buffer limit');
}

"""
if (ROOT / "src/userScript.js").read_text(encoding="utf-8").count(old_buffer) != 1:
    raise RuntimeError("userScript.js: custom buffer-limit startup block not found exactly once")
replace_once("src/userScript.js", old_buffer, "")

# THUMBNAIL FIRST-PAINT FIX:
# The initial Home can be rendered from bootstrap data before our JSON.parse
# hook sees that response. Reuse the existing verifier/promotion engine by
# seeding it from rendered thumbnail video IDs. No new quality algorithm.
thumb_path = ROOT / "src/thumbnail-quality.js"
thumb = thumb_path.read_text(encoding="utf-8")

marker = """// --- Lifecycle ------------------------------------------------------------

function handleVisibilityChange() {
"""
insert = r"""// --- PMCN initial Home bootstrap bridge -----------------------------------
// On a cold launch, YouTube can materialise the first Home from bootstrap data
// that never passes through the JSON.parse hook. The normal quality engine then
// has nothing to probe until the user changes tabs. Seed the SAME existing
// probe/promotion pipeline from the thumbnails already rendered on screen.
//
// This does not invent URLs, dimensions or a second quality policy. It only
// supplies video IDs to scheduleProbe()/qualityCache/pendingPromotions, then
// runPromotionSweep() performs the exact same promotion used after navigation.

let pmcnBootstrapScanTimer = null;
let pmcnBootstrapScanIndex = 0;
const PMCN_BOOTSTRAP_DELAYS = [180, 500, 1000, 1800, 3000];
const PMCN_BOOTSTRAP_MAX_IDS = 36;

function pmcnSeedRenderedThumbnailIds() {
  if (!enabled || pmcnFixedRank === null || document.hidden) return;

  let nodes;
  try {
    nodes = document.querySelectorAll(DOM_SELECTOR);
  } catch {
    return;
  }

  const seen = new Set();
  for (let i = 0; i < nodes.length && seen.size < PMCN_BOOTSTRAP_MAX_IDS; i++) {
    const element = nodes[i];
    const background = element.style && element.style.backgroundImage;
    if (!background) continue;

    const match = THUMB_IN_CSS_RE.exec(background);
    if (!match) continue;

    const videoId = match[1];
    if (seen.has(videoId)) continue;
    seen.add(videoId);

    const cached = qualityCache.get(videoId);
    if (cached !== undefined) {
      pendingPromotions.set(videoId, cached);
    } else {
      scheduleProbe(videoId);
    }
  }

  // Cached results can be promoted immediately. Unknown results go through the
  // existing probe queue and will call runPromotionSweep() on completion.
  if (pendingPromotions.size > 0 && !promoteTimer) {
    promoteTimer = setTimeout(runPromotionSweep, PROMOTION_DEBOUNCE);
  }

  if (probeQueue.size > 0) {
    urgentBudget = Math.max(urgentBudget, PROBE_URGENT_BURST);
    visibleBudget = Math.max(visibleBudget, PROBE_VISIBLE_BURST);
    drainProbes();
  }
}

function pmcnScheduleNextBootstrapScan() {
  if (pmcnBootstrapScanIndex >= PMCN_BOOTSTRAP_DELAYS.length) return;
  const delay = PMCN_BOOTSTRAP_DELAYS[pmcnBootstrapScanIndex++];
  pmcnBootstrapScanTimer = setTimeout(() => {
    pmcnBootstrapScanTimer = null;
    pmcnSeedRenderedThumbnailIds();
    pmcnScheduleNextBootstrapScan();
  }, delay);
}

if (enabled && pmcnFixedRank !== null) {
  pmcnScheduleNextBootstrapScan();
}

// --- Lifecycle ------------------------------------------------------------

function handleVisibilityChange() {
"""
if thumb.count(marker) != 1:
    raise RuntimeError("thumbnail-quality.js: lifecycle marker not found exactly once")
thumb = thumb.replace(marker, insert, 1)
thumb_path.write_text(thumb, encoding="utf-8")

# Version only.
app = ROOT / "assets/appinfo.json"
obj = json.loads(app.read_text(encoding="utf-8"))
obj["version"] = "0.9.4"
app.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

pkg = ROOT / "package.json"
pobj = json.loads(pkg.read_text(encoding="utf-8"))
pobj["version"] = "0.9.4"
pkg.write_text(json.dumps(pobj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Static validation.
us = (ROOT / "src/userScript.js").read_text(encoding="utf-8")
tq = thumb_path.read_text(encoding="utf-8")

assert "initBufferLimit" not in us
assert "hooks/buffer-limit.js" not in us
assert "pmcnSeedRenderedThumbnailIds" in tq
assert "scheduleProbe(videoId)" in tq
assert "pendingPromotions.set(videoId, cached)" in tq
assert "runPromotionSweep" in tq
assert "PMCN_BOOTSTRAP_DELAYS" in tq
assert json.loads(app.read_text(encoding="utf-8"))["version"] == "0.9.4"

print("PMCN UK6530 0.9.4 two-bug surgical delta applied.")
