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

def write(path, content):
    (ROOT / path).write_text(content, encoding="utf-8")

# -------------------------------------------------------------------------
# 0.8.19 — fix thumbnail aspect-ratio/metadata handling.
# - remove obsolete PMCN card-width synchronizer from runtime
# - keep ONLY 16:9 manual thumbnail modes
# - use server-provided high-res 16:9 variants when available
# - never fall back from a 16:9 request to 4:3 hqdefault/sddefault
# - keep URL dimensions consistent with the selected image
# No navigation, icons, Recents, adblock, player or watch-text rules change.
# -------------------------------------------------------------------------

# 1) Blue-button menu: only geometrically safe 16:9 modes.
menu = r"""const STORAGE_KEY = 'pmcn-thumbnail-quality-v1';
const ENGINE_CACHE_KEY = 'ytaf-thumb-quality-16x9-v1';
const OLD_ENGINE_CACHE_KEY = 'ytaf-thumb-quality';

const MODES = [
  { id: 'native', label: 'Nativo (YouTube)' },
  { id: 'mqdefault', label: '320×180 (16:9)' },
  { id: 'hq720', label: '1280×720 (16:9)' },
  { id: 'maxresdefault', label: 'Máxima (16:9)' }
];

const MODE_BY_ID = new Map(MODES.map((m) => [m.id, m]));
let currentMode = loadMode();
let overlay = null;
let cursor = Math.max(0, MODES.findIndex((m) => m.id === currentMode));

function loadMode() {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved && MODE_BY_ID.has(saved)) return saved;

    // Old 4:3 choices are deliberately retired. Do not silently stretch them.
    if (saved === 'default' || saved === 'hqdefault' || saved === 'sddefault') {
      window.localStorage.setItem(STORAGE_KEY, 'native');
    }
  } catch {}
  return 'native';
}

function saveMode(id) {
  currentMode = MODE_BY_ID.has(id) ? id : 'native';
  try {
    window.localStorage.setItem(STORAGE_KEY, currentMode);
    // A change of requested rung must never reuse a decision made by an older
    // engine that could have cached a 4:3 fallback.
    window.localStorage.removeItem(ENGINE_CACHE_KEY);
    window.localStorage.removeItem(OLD_ENGINE_CACHE_KEY);
  } catch {}
}

function isBlueKey(evt) {
  const code = evt.keyCode || evt.which || 0;
  const key = evt.key || evt.code || '';
  return code === 406 || key === 'ColorF3Blue' || key === 'Blue';
}

function isUp(evt) {
  const code = evt.keyCode || evt.which || 0;
  return code === 38 || evt.key === 'ArrowUp';
}

function isDown(evt) {
  const code = evt.keyCode || evt.which || 0;
  return code === 40 || evt.key === 'ArrowDown';
}

function isEnter(evt) {
  const code = evt.keyCode || evt.which || 0;
  return code === 13 || evt.key === 'Enter';
}

function isBack(evt) {
  const code = evt.keyCode || evt.which || 0;
  return code === 461 || code === 27 || evt.key === 'Escape' ||
    evt.key === 'Backspace' || evt.key === 'GoBack';
}

function destroyOverlay() {
  if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay);
  overlay = null;
}

function renderMenu() {
  destroyOverlay();

  overlay = document.createElement('div');
  overlay.id = 'pmcn-thumbnail-quality-menu';
  overlay.style.cssText = [
    'position:fixed',
    'z-index:2147483647',
    'left:50%',
    'top:50%',
    'transform:translate(-50%,-50%)',
    'width:620px',
    'max-width:82vw',
    'background:rgba(14,14,14,.96)',
    'color:#fff',
    'border-radius:18px',
    'padding:28px 30px 24px',
    'box-shadow:0 16px 50px rgba(0,0,0,.55)',
    'font-family:Arial,sans-serif'
  ].join(';');

  const title = document.createElement('div');
  title.textContent = 'Qualidade das capas';
  title.style.cssText = 'font-size:30px;font-weight:700;margin-bottom:8px';
  overlay.appendChild(title);

  const subtitle = document.createElement('div');
  subtitle.textContent = '↑ ↓ escolher   •   OK aplicar   •   Voltar fechar';
  subtitle.style.cssText = 'font-size:18px;opacity:.72;margin-bottom:20px';
  overlay.appendChild(subtitle);

  const list = document.createElement('div');

  MODES.forEach((mode, index) => {
    const row = document.createElement('div');
    const selected = index === cursor;
    const active = mode.id === currentMode;

    row.style.cssText = [
      'padding:13px 16px',
      'margin:5px 0',
      'border-radius:10px',
      'font-size:24px',
      'display:flex',
      'justify-content:space-between',
      'background:' + (selected ? 'rgba(255,255,255,.18)' : 'transparent'),
      'outline:' + (selected ? '2px solid rgba(255,255,255,.9)' : 'none')
    ].join(';');

    const left = document.createElement('span');
    left.textContent = mode.label;
    row.appendChild(left);

    const right = document.createElement('span');
    right.textContent = active ? 'ATUAL' : '';
    right.style.cssText = 'font-size:18px;opacity:.8;align-self:center';
    row.appendChild(right);

    list.appendChild(row);
  });

  overlay.appendChild(list);

  const note = document.createElement('div');
  note.textContent =
    'Somente formatos 16:9. Máxima usa a melhor variante 16:9 disponível por vídeo.';
  note.style.cssText = 'font-size:17px;opacity:.68;margin-top:18px;line-height:1.35';
  overlay.appendChild(note);

  document.documentElement.appendChild(overlay);
}

function updateCursor(delta) {
  cursor = (cursor + delta + MODES.length) % MODES.length;
  renderMenu();
}

function applySelection() {
  const mode = MODES[cursor] || MODES[0];
  saveMode(mode.id);

  if (overlay) {
    overlay.innerHTML = '';

    const msg = document.createElement('div');
    msg.textContent = 'Capas: ' + mode.label;
    msg.style.cssText = 'font-size:30px;font-weight:700;text-align:center;padding:25px';
    overlay.appendChild(msg);

    const sub = document.createElement('div');
    sub.textContent = 'Aplicando…';
    sub.style.cssText = 'font-size:20px;opacity:.7;text-align:center;padding-bottom:25px';
    overlay.appendChild(sub);
  }

  setTimeout(() => window.location.reload(), 300);
}

function onKeyDown(evt) {
  if (!overlay) {
    if (!isBlueKey(evt)) return;
    evt.preventDefault();
    evt.stopPropagation();
    cursor = Math.max(0, MODES.findIndex((m) => m.id === currentMode));
    renderMenu();
    return;
  }

  if (isUp(evt)) {
    evt.preventDefault(); evt.stopPropagation(); updateCursor(-1); return;
  }
  if (isDown(evt)) {
    evt.preventDefault(); evt.stopPropagation(); updateCursor(1); return;
  }
  if (isEnter(evt)) {
    evt.preventDefault(); evt.stopPropagation(); applySelection(); return;
  }
  if (isBack(evt) || isBlueKey(evt)) {
    evt.preventDefault(); evt.stopPropagation(); destroyOverlay();
  }
}

window.addEventListener('keydown', onKeyDown, true);

// Remove stale data from the abandoned card-size experiment.
try { window.localStorage.removeItem('pmcn-subscriptions-card-width-v1'); } catch {}

export {};
"""
write("src/pmcn-thumbnail-quality.js", menu)

# 2) Remove the obsolete card-size synchronizer entirely from runtime/source.
replace_once(
    "src/userScript.js",
    "import './pmcn-card-sync.js';\nimport './pmcn-thumbnail-quality.js';\n",
    "import './pmcn-thumbnail-quality.js';\n"
)
card_sync = ROOT / "src/pmcn-card-sync.js"
if card_sync.exists():
    card_sync.unlink()

# 3) Patch the robust thumbnail engine.
thumb_path = ROOT / "src/thumbnail-quality.js"
thumb = thumb_path.read_text(encoding="utf-8")

# Never reuse a cache written by the old engine, because it could contain a
# 4:3 fallback rank for a video requested in Maximum mode.
old_cache = "const CACHE_KEY = 'ytaf-thumb-quality';"
new_cache = "const CACHE_KEY = 'ytaf-thumb-quality-16x9-v1';"
if thumb.count(old_cache) != 1:
    raise RuntimeError("thumbnail-quality.js: old cache key not found exactly once")
thumb = thumb.replace(old_cache, new_cache, 1)

old_pmcn = r"""// PMCN UK6530 fixed thumbnail selector.
// The UI lives in pmcn-thumbnail-quality.js; this engine reads the persisted
// choice before YouTube response objects reach the renderer.
const PMCN_QUALITY_STORAGE_KEY = 'pmcn-thumbnail-quality-v1';
const PMCN_ALLOWED_MODES = new Set([
  'native',
  'default',
  'mqdefault',
  'hqdefault',
  'sddefault',
  'hq720',
  'maxresdefault'
]);

function readPmcnQualityMode() {
  try {
    const value = window.localStorage.getItem(PMCN_QUALITY_STORAGE_KEY);
    if (value && PMCN_ALLOWED_MODES.has(value)) return value;
  } catch {}
  return 'native';
}

const pmcnQualityMode = readPmcnQualityMode();
const pmcnFixedRank = pmcnQualityMode === 'native' ? null : RANK[pmcnQualityMode];
"""

new_pmcn = r"""// PMCN UK6530 manual thumbnail selector.
// Manual modes are strictly 16:9. A 4:3 derivative must never be stretched
// into the TV app's 16:9 card geometry.
const PMCN_QUALITY_STORAGE_KEY = 'pmcn-thumbnail-quality-v1';
const PMCN_ALLOWED_MODES = new Set([
  'native',
  'mqdefault',
  'hq720',
  'maxresdefault'
]);

function readPmcnQualityMode() {
  try {
    const value = window.localStorage.getItem(PMCN_QUALITY_STORAGE_KEY);
    if (value && PMCN_ALLOWED_MODES.has(value)) return value;
  } catch {}
  return 'native';
}

const pmcnQualityMode = readPmcnQualityMode();
const pmcnFixedRank = pmcnQualityMode === 'native' ? null : RANK[pmcnQualityMode];
const PMCN_16_9_FLOOR = RANK.mqdefault;

function pmcnDimensionsForRank(rank) {
  return rank >= RANK.hq720
    ? { width: 1280, height: 720 }
    : { width: 320, height: 180 };
}

function pmcnApplyDimensions(entry, rank) {
  if (!entry || typeof entry !== 'object') return false;
  const dims = pmcnDimensionsForRank(rank);
  let changed = false;
  if (entry.width !== dims.width) {
    entry.width = dims.width;
    changed = true;
  }
  if (entry.height !== dims.height) {
    entry.height = dims.height;
    changed = true;
  }
  return changed;
}

function pmcnIs16x9(entry) {
  if (!entry || typeof entry.url !== 'string') return false;
  const width = Number(entry.width);
  const height = Number(entry.height);
  if (!(width > 0) || !(height > 0)) return false;
  return Math.abs(width / height - 16 / 9) < 0.06;
}

function pmcnProvidedHigh16x9(list) {
  if (pmcnFixedRank === null || pmcnFixedRank === RANK.mqdefault) return null;

  let best = null;
  for (let i = 0; i < list.length; i++) {
    const entry = list[i];
    if (!pmcnIs16x9(entry)) continue;
    const width = Number(entry.width);
    const height = Number(entry.height);

    // 120/320-wide sources are useful as a safe floor, but they are not proof
    // that the server supplied the high-quality image requested by these modes.
    if (width < 1000 || height < 500) continue;

    if (!best) {
      best = entry;
      continue;
    }

    if (pmcnFixedRank === RANK.maxresdefault) {
      if (width * height > Number(best.width) * Number(best.height)) best = entry;
    } else {
      // For 1280×720 prefer the provided source closest to 1280px wide.
      if (Math.abs(width - 1280) < Math.abs(Number(best.width) - 1280)) best = entry;
    }
  }
  return best;
}

function pmcnApplyProvided(list, source) {
  if (!source) return 0;
  const sourceUrl = source.url;
  const sourceWidth = Number(source.width);
  const sourceHeight = Number(source.height);
  let changed = 0;

  for (let i = 0; i < list.length; i++) {
    const entry = list[i];
    if (!entry || typeof entry !== 'object') continue;
    let entryChanged = false;

    if (entry.url !== sourceUrl) {
      entry.url = sourceUrl;
      entryChanged = true;
    }
    if (entry.width !== sourceWidth) {
      entry.width = sourceWidth;
      entryChanged = true;
    }
    if (entry.height !== sourceHeight) {
      entry.height = sourceHeight;
      entryChanged = true;
    }

    if (entryChanged) changed++;
  }

  return changed;
}
"""

if thumb.count(old_pmcn) != 1:
    raise RuntimeError("thumbnail-quality.js: PMCN mode block not found exactly once")
thumb = thumb.replace(old_pmcn, new_pmcn, 1)

old_fixed = r"""  // PMCN fixed mode: rewrite every thumbnail URL in the schema-aware
  // containers to one CLEAN YouTube derivative. We intentionally do NOT carry
  // the old URL query string: those parameters can preserve a lower resize /
  // transform and were the reason 0.8.15 appeared unchanged.
  if (pmcnFixedRank !== null) {
    const verified = qualityCache.get(videoId);
    let target = pmcnFixedRank;

    // Higher derivatives are not present for every upload. Show the requested
    // rung immediately, then let the existing idle verifier correct only the
    // videos where that derivative genuinely does not exist.
    const needsProbe = target > GUARANTEED_RANK && verified === undefined;
    if (needsProbe) scheduleProbe(videoId);
    if (verified !== undefined && verified < target) target = verified;

    const next = buildUrl(videoId, QUALITY_NAMES[target], true);
    if (next === url) return 0;
    entry.url = next;

    if (needsProbe) {
      const knownFloor = proven === undefined ? GUARANTEED_RANK : proven;
      trackPending(videoId, entry, Math.min(knownFloor, pmcnFixedRank));
    }
    return 1;
  }

"""

new_fixed = r"""  // PMCN manual mode. URL and metadata are changed together. This is the
  // important difference from 0.8.16: a 16:9 maxres/hq720 URL must never keep
  // 4:3 width/height metadata from the source entry.
  if (pmcnFixedRank !== null) {
    const verified = qualityCache.get(videoId);
    let target = pmcnFixedRank;

    const needsProbe =
      target >= RANK.hq720 &&
      verified === undefined;

    if (needsProbe) scheduleProbe(videoId);

    if (verified !== undefined) {
      if (target === RANK.maxresdefault) {
        target = verified >= RANK.hq720
          ? Math.min(target, verified)
          : PMCN_16_9_FLOOR;
      } else if (target === RANK.hq720) {
        target = verified >= RANK.hq720
          ? RANK.hq720
          : PMCN_16_9_FLOOR;
      }
    }

    const next = buildUrl(videoId, QUALITY_NAMES[target], true);
    let changed = 0;
    if (next !== url) {
      entry.url = next;
      changed = 1;
    }
    if (pmcnApplyDimensions(entry, target)) changed = 1;

    if (needsProbe) {
      // Manual 16:9 mode has an explicit 16:9 floor. Never inherit a proven
      // 4:3 hqdefault/sddefault rank from the response container.
      trackPending(videoId, entry, PMCN_16_9_FLOOR);
    }

    return changed;
  }

"""

if thumb.count(old_fixed) != 1:
    raise RuntimeError("thumbnail-quality.js: old PMCN fixed branch not found exactly once")
thumb = thumb.replace(old_fixed, new_fixed, 1)

# If YouTube already supplied a high-res 16:9 URL in the container, preserve
# that exact server URL/crop instead of inventing a generic basename.
container_marker = """  const list = container.thumbnails || container.sources;
  if (!Array.isArray(list) || list.length === 0) return 0;

"""
container_insert = container_marker + """  if (pmcnFixedRank !== null) {
    const provided = pmcnProvidedHigh16x9(list);
    if (provided) return pmcnApplyProvided(list, provided);
  }

"""
if thumb.count(container_marker) != 1:
    raise RuntimeError("thumbnail-quality.js: upgradeContainer marker not found exactly once")
thumb = thumb.replace(container_marker, container_insert, 1)

old_resolve = r"""async function resolveQuality(videoId, onScreen) {
  // On screen: the browser already holds the answer, so ask it. Off screen: a
  // HEAD, because an <img> there would pull down a full image nobody is looking
  // at - the correction path only has to be exact for tiles that are visible.
  const check = onScreen ? imageExists : headExists;

  if (pmcnFixedRank !== null && pmcnFixedRank > GUARANTEED_RANK) {
    for (let rank = pmcnFixedRank; rank > GUARANTEED_RANK; rank--) {
      if (await check(buildUrl(videoId, QUALITY_NAMES[rank], true))) return rank;
      if (!enabled) break;
    }
    return GUARANTEED_RANK;
  }

  for (let i = 0; i < PROBE_LADDER.length; i++) {
    const rank = PROBE_LADDER[i];
    if (await check(buildUrl(videoId, QUALITY_NAMES[rank]))) return rank;
    if (!enabled) break;
  }
  return FLOOR_RANK;
}
"""

new_resolve = r"""async function resolveQuality(videoId, onScreen) {
  // On screen: the browser already holds the answer, so ask it. Off screen: a
  // HEAD, because an <img> there would pull down a full image nobody is looking
  // at - the correction path only has to be exact for tiles that are visible.
  const check = onScreen ? imageExists : headExists;

  if (pmcnFixedRank !== null) {
    if (pmcnFixedRank === RANK.maxresdefault) {
      if (await check(buildUrl(videoId, QUALITY_NAMES[RANK.maxresdefault], true))) {
        return RANK.maxresdefault;
      }
      if (enabled && await check(buildUrl(videoId, QUALITY_NAMES[RANK.hq720], true))) {
        return RANK.hq720;
      }
      return PMCN_16_9_FLOOR;
    }

    if (pmcnFixedRank === RANK.hq720) {
      if (await check(buildUrl(videoId, QUALITY_NAMES[RANK.hq720], true))) {
        return RANK.hq720;
      }
      return PMCN_16_9_FLOOR;
    }

    return PMCN_16_9_FLOOR;
  }

  for (let i = 0; i < PROBE_LADDER.length; i++) {
    const rank = PROBE_LADDER[i];
    if (await check(buildUrl(videoId, QUALITY_NAMES[rank]))) return rank;
    if (!enabled) break;
  }
  return FLOOR_RANK;
}
"""

if thumb.count(old_resolve) != 1:
    raise RuntimeError("thumbnail-quality.js: old resolveQuality block not found exactly once")
thumb = thumb.replace(old_resolve, new_resolve, 1)

old_apply = r"""function applyCorrection(videoId, rank) {
  const entries = pendingEntries.get(videoId);
  if (!entries) return;
  pendingEntries.delete(videoId);
  const url = buildUrl(videoId, QUALITY_NAMES[rank], rank <= GUARANTEED_RANK);
  for (let i = 0; i < entries.length; i++) {
    if (entries[i] && entries[i].url !== url) entries[i].url = url;
  }
}
"""

new_apply = r"""function applyCorrection(videoId, rank) {
  const entries = pendingEntries.get(videoId);
  if (!entries) return;
  pendingEntries.delete(videoId);
  const forceJpeg = pmcnFixedRank !== null ? true : rank <= GUARANTEED_RANK;
  const url = buildUrl(videoId, QUALITY_NAMES[rank], forceJpeg);
  for (let i = 0; i < entries.length; i++) {
    const entry = entries[i];
    if (!entry) continue;
    if (entry.url !== url) entry.url = url;
    if (pmcnFixedRank !== null) pmcnApplyDimensions(entry, rank);
  }
}
"""

if thumb.count(old_apply) != 1:
    raise RuntimeError("thumbnail-quality.js: applyCorrection block not found exactly once")
thumb = thumb.replace(old_apply, new_apply, 1)

old_probe_done = """  const resolved = typeof rank === 'number' ? rank : FLOOR_RANK;"""
new_probe_done = """  const fallbackRank = pmcnFixedRank !== null ? PMCN_16_9_FLOOR : FLOOR_RANK;
  const resolved = typeof rank === 'number' ? rank : fallbackRank;"""
if thumb.count(old_probe_done) != 1:
    raise RuntimeError("thumbnail-quality.js: probe fallback line not found exactly once")
thumb = thumb.replace(old_probe_done, new_probe_done, 1)

old_promotion_url = """    const next = buildUrl(match[1], QUALITY_NAMES[rank], rank === FLOOR_RANK);"""
new_promotion_url = """    const next = buildUrl(
      match[1],
      QUALITY_NAMES[rank],
      pmcnFixedRank !== null ? true : rank === FLOOR_RANK
    );"""
if thumb.count(old_promotion_url) != 1:
    raise RuntimeError("thumbnail-quality.js: promotion URL line not found exactly once")
thumb = thumb.replace(old_promotion_url, new_promotion_url, 1)

thumb_path.write_text(thumb, encoding="utf-8")

# 4) Version only.
app = ROOT / "assets/appinfo.json"
obj = json.loads(app.read_text(encoding="utf-8"))
obj["version"] = "0.8.19"
app.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

pkg = ROOT / "package.json"
pobj = json.loads(pkg.read_text(encoding="utf-8"))
pobj["version"] = "0.8.19"
pkg.write_text(json.dumps(pobj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# 5) Scope/static verification.
us = (ROOT / "src/userScript.js").read_text(encoding="utf-8")
menu_js = (ROOT / "src/pmcn-thumbnail-quality.js").read_text(encoding="utf-8")
thumb_js = thumb_path.read_text(encoding="utf-8")
ad = (ROOT / "src/adblock.js").read_text(encoding="utf-8")

assert "import './pmcn-card-sync.js';" not in us
assert not (ROOT / "src/pmcn-card-sync.js").exists()
assert "import './pmcn-thumbnail-quality.js';" in us

for bad in ["120×90", "480×360", "640×480"]:
    assert bad not in menu_js
for good in ["320×180 (16:9)", "1280×720 (16:9)", "Máxima (16:9)"]:
    assert good in menu_js

assert "ytaf-thumb-quality-16x9-v1" in thumb_js
assert "PMCN_16_9_FLOOR = RANK.mqdefault" in thumb_js
assert "pmcnApplyDimensions" in thumb_js
assert "pmcnProvidedHigh16x9" in thumb_js
assert "return PMCN_16_9_FLOOR;" in thumb_js
assert "RANK.sddefault" not in thumb_js[thumb_js.index("async function resolveQuality"):thumb_js.index("function scheduleProbe")]
assert "UK6530_BLOCKED_NAV_BROWSE_IDS" in ad
assert json.loads(app.read_text(encoding="utf-8"))["version"] == "0.8.19"

print("PMCN UK6530 0.8.19 16:9 thumbnail correction applied successfully.")
