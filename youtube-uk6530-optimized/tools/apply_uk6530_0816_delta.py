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
# 0.8.16 — keep the blue-button menu, but replace the simplified thumbnail
# rewriter with the project's original schema-aware thumbnail engine.
# No menu-navigation, card-layout, icon, Recents or splash logic is changed.
# -------------------------------------------------------------------------

# 1) The blue-button file becomes UI/state only. The actual rewrite is done by
#    thumbnail-quality.js, which already knows the current YouTube TV schemas.
menu = r"""const STORAGE_KEY = 'pmcn-thumbnail-quality-v1';

const MODES = [
  { id: 'native', label: 'Nativo (YouTube)' },
  { id: 'default', label: '120×90' },
  { id: 'mqdefault', label: '320×180' },
  { id: 'hqdefault', label: '480×360' },
  { id: 'sddefault', label: '640×480' },
  { id: 'hq720', label: '1280×720' },
  { id: 'maxresdefault', label: 'Máxima' }
];

const MODE_BY_ID = new Map(MODES.map((m) => [m.id, m]));
let currentMode = loadMode();
let overlay = null;
let cursor = Math.max(0, MODES.findIndex((m) => m.id === currentMode));

function loadMode() {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved && MODE_BY_ID.has(saved)) return saved;
  } catch {}
  return 'native';
}

function saveMode(id) {
  currentMode = MODE_BY_ID.has(id) ? id : 'native';
  try {
    window.localStorage.setItem(STORAGE_KEY, currentMode);
    window.localStorage.removeItem('ytaf-thumb-quality');
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
  return code === 461 || code === 27 || evt.key === 'Escape' || evt.key === 'Backspace' || evt.key === 'GoBack';
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
  note.textContent = 'A escolha fica salva. Ao aplicar, o YouTube recarrega uma vez para usar a nova qualidade.';
  note.style.cssText = 'font-size:17px;opacity:.62;margin-top:18px;line-height:1.35';
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
    evt.preventDefault();
    evt.stopPropagation();
    updateCursor(-1);
    return;
  }

  if (isDown(evt)) {
    evt.preventDefault();
    evt.stopPropagation();
    updateCursor(1);
    return;
  }

  if (isEnter(evt)) {
    evt.preventDefault();
    evt.stopPropagation();
    applySelection();
    return;
  }

  if (isBack(evt) || isBlueKey(evt)) {
    evt.preventDefault();
    evt.stopPropagation();
    destroyOverlay();
  }
}

window.addEventListener('keydown', onKeyDown, true);

export {};
"""
write("src/pmcn-thumbnail-quality.js", menu)

# 2) Remove the broken generic tree rewriter from adblock and restore the
#    project's schema-aware thumbnail engine.
replace_once(
    "src/adblock.js",
    "import { configGetAll, configAddChangeListener } from './config';\nimport { rewriteThumbnailQuality } from './pmcn-thumbnail-quality.js';\n",
    "import { configGetAll, configAddChangeListener } from './config';\nimport { upgradeResponseThumbnails, thumbnailHookRequired } from './thumbnail-quality.js';\n"
)

replace_once(
    "src/adblock.js",
    """    // PMCN: optional user-selected thumbnail quality. Native mode is a no-op.
    rewriteThumbnailQuality(data);

""",
    """    // PMCN: schema-aware thumbnail rewrite. Native mode is a no-op.
    if (thumbnailHookRequired()) upgradeResponseThumbnails(data, responseType);

"""
)

replace_once(
    "src/adblock.js",
    """    cfgSnapshot[CONFIG_KEYS.ENDCARDS] ||
    cfgEmojiFixEffective
""",
    """    cfgSnapshot[CONFIG_KEYS.ENDCARDS] ||
    cfgEmojiFixEffective ||
    thumbnailHookRequired()
"""
)

# 3) Keep the blue-button UI loaded explicitly. In 0.8.15 it was pulled in
#    indirectly by adblock; 0.8.16 removes that dependency.
replace_once(
    "src/userScript.js",
    "import './pmcn-card-sync.js';\n",
    "import './pmcn-card-sync.js';\nimport './pmcn-thumbnail-quality.js';\n"
)

# 4) Teach the original robust engine to obey our persisted blue-menu mode.
thumb_path = ROOT / "src/thumbnail-quality.js"
thumb = thumb_path.read_text(encoding="utf-8")

rank_marker = """const RANK = { default: 0, mqdefault: 1, hqdefault: 2, sddefault: 3, hq720: 4, maxresdefault: 5 };
"""
pmcn_block = rank_marker + r"""

// PMCN UK6530 fixed thumbnail selector.
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
if thumb.count(rank_marker) != 1:
    raise RuntimeError("thumbnail-quality.js: RANK marker not found exactly once")
thumb = thumb.replace(rank_marker, pmcn_block, 1)

old_enabled = "let enabled = !!configRead('upgradeThumbnails');"
new_enabled = """// PMCN selector owns enablement in this Lite build. Native means zero rewrite.
let enabled = pmcnFixedRank !== null;"""
if thumb.count(old_enabled) != 1:
    raise RuntimeError("thumbnail-quality.js: enabled marker not found exactly once")
thumb = thumb.replace(old_enabled, new_enabled, 1)

upgrade_marker = """  const verified = qualityCache.get(videoId);
"""
fixed_branch = r"""  // PMCN fixed mode: rewrite every thumbnail URL in the schema-aware
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

""" + upgrade_marker
if thumb.count(upgrade_marker) != 1:
    raise RuntimeError("thumbnail-quality.js: upgrade insertion marker not found exactly once")
thumb = thumb.replace(upgrade_marker, fixed_branch, 1)

# For explicit 640/720/max modes, verify the selected derivative and fall
# back through lower high-quality rungs instead of leaving a grey thumbnail.
old_resolve = """async function resolveQuality(videoId, onScreen) {
  // On screen: the browser already holds the answer, so ask it. Off screen: a
  // HEAD, because an <img> there would pull down a full image nobody is looking
  // at - the correction path only has to be exact for tiles that are visible.
  const check = onScreen ? imageExists : headExists;
  for (let i = 0; i < PROBE_LADDER.length; i++) {
    const rank = PROBE_LADDER[i];
    if (await check(buildUrl(videoId, QUALITY_NAMES[rank]))) return rank;
    if (!enabled) break;
  }
  return FLOOR_RANK;
}
"""
new_resolve = """async function resolveQuality(videoId, onScreen) {
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
if thumb.count(old_resolve) != 1:
    raise RuntimeError("thumbnail-quality.js: resolveQuality block not found exactly once")
thumb = thumb.replace(old_resolve, new_resolve, 1)

# The old config switch must not disable the blue-menu mode in the Lite build.
old_listener = """configAddChangeListener('upgradeThumbnails', (evt) => {
  enabled = !!evt.detail.newValue;
  if (enabled) loadCache();
  else cleanup();
});"""
new_listener = """configAddChangeListener('upgradeThumbnails', () => {
  // PMCN Lite: the blue-button persisted mode is authoritative.
  enabled = pmcnFixedRank !== null;
  if (enabled) loadCache();
  else cleanup();
});"""
if thumb.count(old_listener) != 1:
    raise RuntimeError("thumbnail-quality.js: upgradeThumbnails listener not found exactly once")
thumb = thumb.replace(old_listener, new_listener, 1)

thumb_path.write_text(thumb, encoding="utf-8")

# 5) Keep all existing UX / menus / icons untouched; only bump version.
app = ROOT / "assets/appinfo.json"
obj = json.loads(app.read_text(encoding="utf-8"))
obj["version"] = "0.8.16"
app.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

pkg = ROOT / "package.json"
pobj = json.loads(pkg.read_text(encoding="utf-8"))
pobj["version"] = "0.8.16"
pkg.write_text(json.dumps(pobj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# 6) Static verification of scope and engine wiring.
ad = (ROOT / "src/adblock.js").read_text(encoding="utf-8")
menu_js = (ROOT / "src/pmcn-thumbnail-quality.js").read_text(encoding="utf-8")
thumb_js = thumb_path.read_text(encoding="utf-8")

assert "rewriteThumbnailQuality" not in ad
assert "upgradeResponseThumbnails" in ad
assert "thumbnailHookRequired" in ad
assert "UK6530_BLOCKED_NAV_BROWSE_IDS" in ad
assert "FEgaming_destination" in ad
assert "FEpodcasts_destination" in ad
assert "FEstorefront" in ad
assert "ColorF3Blue" in menu_js
assert "removeItem('ytaf-thumb-quality')" in menu_js
assert "rewriteThumbnailQuality" not in menu_js
assert "import './pmcn-thumbnail-quality.js';" in (ROOT / "src/userScript.js").read_text(encoding="utf-8")
assert "PMCN_QUALITY_STORAGE_KEY" in thumb_js
assert "pmcnFixedRank" in thumb_js
assert "entry.url = next;" in thumb_js
assert "Math.min(knownFloor, pmcnFixedRank)" in thumb_js
assert "for (let rank = pmcnFixedRank; rank > GUARANTEED_RANK; rank--)" in thumb_js
assert json.loads(app.read_text(encoding="utf-8"))["version"] == "0.8.16"

print("PMCN UK6530 0.8.16 robust thumbnail engine applied successfully.")
