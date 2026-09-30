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
# PMCN thumbnail quality selector.
# Blue remote button opens a lightweight menu.
# Selection is persisted and applied to future InnerTube responses.
# -------------------------------------------------------------------------
thumb = r"""const STORAGE_KEY = 'pmcn-thumbnail-quality-v1';

const MODES = [
  { id: 'native', label: 'Nativo (YouTube)', basename: null, approx: '' },
  { id: 'default', label: '120×90', basename: 'default', approx: '120×90' },
  { id: 'mqdefault', label: '320×180', basename: 'mqdefault', approx: '320×180' },
  { id: 'hqdefault', label: '480×360', basename: 'hqdefault', approx: '480×360' },
  { id: 'sddefault', label: '640×480', basename: 'sddefault', approx: '640×480' },
  { id: 'hq720', label: '1280×720', basename: 'hq720', approx: '1280×720' },
  { id: 'maxresdefault', label: 'Máxima', basename: 'maxresdefault', approx: 'máxima disponível' }
];

const MODE_BY_ID = new Map(MODES.map((m) => [m.id, m]));

function parseThumbnailUrl(url) {
  if (typeof url !== 'string') return null;

  const jpegPrefix = 'https://i.ytimg.com/vi/';
  const webpPrefix = 'https://i.ytimg.com/vi_webp/';
  let rest = null;

  if (url.indexOf(jpegPrefix) === 0) rest = url.slice(jpegPrefix.length);
  else if (url.indexOf(webpPrefix) === 0) rest = url.slice(webpPrefix.length);
  else return null;

  const slash = rest.indexOf('/');
  if (slash <= 0) return null;

  const videoId = rest.slice(0, slash);
  const fileAndQuery = rest.slice(slash + 1);
  const q = fileAndQuery.indexOf('?');
  const query = q >= 0 ? fileAndQuery.slice(q) : '';

  return { videoId, query };
}

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
  try { window.localStorage.setItem(STORAGE_KEY, currentMode); } catch {}
}

export function getThumbnailQualityMode() {
  return currentMode;
}

export function rewriteThumbnailQuality(root) {
  const mode = MODE_BY_ID.get(currentMode);
  if (!mode || !mode.basename || !root || typeof root !== 'object') return 0;

  const queue = [root, 0];
  let pos = 0;
  let visited = 0;
  let changed = 0;
  const maxNodes = 7000;
  const maxDepth = 16;

  while (pos < queue.length && visited < maxNodes) {
    const node = queue[pos++];
    const depth = queue[pos++];
    visited++;

    if (!node || typeof node !== 'object' || depth > maxDepth) continue;

    if (typeof node.url === 'string' && node.url.indexOf('i.ytimg.com/vi') !== -1) {
      const parsed = parseThumbnailUrl(node.url);
      if (parsed) {
        const next =
          'https://i.ytimg.com/vi/' +
          parsed.videoId +
          '/' +
          mode.basename +
          '.jpg' +
          parsed.query;

        if (next !== node.url) {
          node.url = next;
          changed++;
        }
      }
    }

    const nextDepth = depth + 1;
    if (Array.isArray(node)) {
      for (let i = 0; i < node.length; i++) {
        const v = node[i];
        if (v && typeof v === 'object') queue.push(v, nextDepth);
      }
    } else {
      for (const k in node) {
        const v = node[k];
        if (v && typeof v === 'object') queue.push(v, nextDepth);
      }
    }
  }

  return changed;
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
    row.setAttribute('data-index', String(index));
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

export {};
"""
write("src/pmcn-thumbnail-quality.js", thumb)

# Integrate the rewriter into the existing JSON.parse hook.
replace_once(
    "src/adblock.js",
    "import { configGetAll, configAddChangeListener } from './config';\n",
    "import { configGetAll, configAddChangeListener } from './config';\nimport { rewriteThumbnailQuality } from './pmcn-thumbnail-quality.js';\n"
)

needle = """    if (cfgFlags.enableTrackingBlock) {
"""
replacement = """    // PMCN: optional user-selected thumbnail quality. Native mode is a no-op.
    rewriteThumbnailQuality(data);

""" + needle
replace_once("src/adblock.js", needle, replacement)

# Remove local custom splash so only the remote YouTube loading screen remains.
app = ROOT / "assets/appinfo.json"
obj = json.loads(app.read_text(encoding="utf-8"))
obj["version"] = "0.8.15"
obj.pop("splashBackground", None)
app.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

pkg = ROOT / "package.json"
pobj = json.loads(pkg.read_text(encoding="utf-8"))
pobj["version"] = "0.8.15"
pkg.write_text(json.dumps(pobj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Validation
ad = (ROOT / "src/adblock.js").read_text(encoding="utf-8")
menu = (ROOT / "src/pmcn-thumbnail-quality.js").read_text(encoding="utf-8")
assert "rewriteThumbnailQuality(data);" in ad
assert "ColorF3Blue" in menu
for q in ["default", "mqdefault", "hqdefault", "sddefault", "hq720", "maxresdefault"]:
    assert q in menu
assert '"splashBackground"' not in app.read_text(encoding="utf-8")
assert json.loads(app.read_text(encoding="utf-8"))["version"] == "0.8.15"
print("PMCN UK6530 0.8.15 thumbnail selector applied.")
