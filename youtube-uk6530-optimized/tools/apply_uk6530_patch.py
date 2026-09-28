#!/usr/bin/env python3
"""
PMCN YouTube UK6530 v0.3.3 — sem zoom da prateleira em foco.

Base: v0.3.1.
- mantém o layout original do YouTube por padrão;
- mede a largura REAL dos cards da aba Inscrições na própria TV;
- salva essa largura localmente;
- usa exatamente essa largura apenas nos cards da aba Início;
- não fixa 18rem nem inventa uma dimensão;
- mantém menu lateral enxuto, adblock, thumbnails leves, AV1 evitado e buffer de 20 s.
"""

from pathlib import Path
import json

ROOT = Path.cwd()

def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    data = p.read_text(encoding="utf-8")
    count = data.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: esperado 1 trecho para substituir, encontrado {count}")
    p.write_text(data.replace(old, new, 1), encoding="utf-8")

def remove_once(path: str, text: str) -> None:
    replace_once(path, text, "")

def append_text(path: str, text: str) -> None:
    p = ROOT / path
    data = p.read_text(encoding="utf-8")
    if text.strip() in data:
        raise RuntimeError(f"{path}: bloco já existe")
    p.write_text(data.rstrip() + "\n\n" + text.strip() + "\n", encoding="utf-8")

def write_text(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")

def require_contains(path: str, needle: str) -> None:
    data = (ROOT / path).read_text(encoding="utf-8")
    if needle not in data:
        raise RuntimeError(f"{path}: validação falhou; trecho ausente: {needle}")

def require_absent(path: str, needle: str) -> None:
    data = (ROOT / path).read_text(encoding="utf-8")
    if needle in data:
        raise RuntimeError(f"{path}: validação falhou; trecho ainda presente: {needle}")

# 1) Perfil fixo Lite
profile_marker = "let localConfig = Object.assign({}, defaultConfig, loadStoredConfig() || {});"
profile_block = profile_marker + r"""

// PMCN UK6530 LITE v3.3 -----------------------------------------------------
const UK6530_LITE_PROFILE = {
  enableAdBlock: true,
  enableTrackingBlock: false,
  enableReturnYouTubeDislike: false,
  upgradeThumbnails: false,
  removeGlobalShorts: true,
  removeLiveVideos: true,
  removeTopLiveGames: true,
  removeMostRelevant: false,
  enableSponsorBlock: false,
  showWatch: false,
  enableOledCareMode: false,
  forceHighResVideo: false,
  forceVideoCodec: 'no_av1',
  enableLegacyEmojiFix: false,
  hideEndcards: true,
  disableNotifications: true,
  forcePreviews: 'force_off'
};

Object.assign(localConfig, UK6530_LITE_PROFILE);
try {
  window.localStorage.setItem(CONFIG_KEY, JSON.stringify(localConfig));
  window.localStorage.setItem('pmcn-uk6530-profile', 'lite-v3.3');
} catch {}
"""
replace_once("src/config.js", profile_marker, profile_block)

replace_once(
    "src/config.js",
    "export function configWrite(key, value) {\n  if (!configExists(key)) throw new Error('tried to write unknown config key: ' + key);",
    "export function configWrite(key, value) {\n  if (!configExists(key)) throw new Error('tried to write unknown config key: ' + key);\n  if (key === 'enableAdBlock') value = true;"
)

# 2) Cortes do bundle Lite
for line in [
    "import './ui.js'; // Registers the green-key handler, options panel, video-quality, global styles\n",
    "import './sponsorblock.js';\n",
    "import './emoji-font.js';\n",
    "import './watch.js';\n",
]:
    remove_once("src/userScript.js", line)

replace_once(
    "src/userScript.js",
    "initBufferLimit();\n\tconsole.info('Initiating buffer limit');",
    "initBufferLimit({ retainBehindSecs: 20, minTrimSecs: 10, trimIntervalMs: 5000 });\n\tconsole.info('Initiating UK6530 Lite buffer limit');"
)

# 3) Sem Max Thumbnail Quality
remove_once(
    "src/adblock.js",
    "import { upgradeResponseThumbnails, thumbnailHookRequired } from './thumbnail-quality.js';\n"
)
remove_once(
    "src/adblock.js",
    "    if (cfgFlags.upgradeThumbnails) upgradeResponseThumbnails(data, responseType);\n"
)
replace_once(
    "src/adblock.js",
    "    cfgEmojiFixEffective ||\n    thumbnailHookRequired()\n",
    "    cfgEmojiFixEffective\n"
)

# 4) Filtro JSON robusto de navegação
ui_strings_end = """const UI_STRINGS = {
  SHORTS_TITLE: 'Shorts',
  TOP_LIVE_GAMES_TITLE: 'Top live games',
  MOST_RELEVANT_TITLE: 'Most relevant',
  GUEST_PROMPT_TEXT: 'Sign in for better recommendations'
};
"""
nav_block = ui_strings_end + r"""

const UK6530_BLOCKED_NAV_TITLES = new Set([
  'jogos', 'games', 'gaming',
  'musica', 'music',
  'esportes', 'sports',
  'podcast', 'podcasts',
  'noticias', 'news',
  'filmes', 'movies', 'movies & tv',
  'ao vivo', 'live'
]);

function normalizeUK6530NavTitle(value) {
  if (!value) return '';
  return String(value)
    .toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}
"""
replace_once("src/adblock.js", ui_strings_end, nav_block)

insert_point = """  if (removeGlobalShorts) {
    const title =
      renderer.title?.simpleText ||
      renderer.title?.runs?.[0]?.text ||
      renderer.tabIdentifier ||
      (typeof renderer.title === 'string' ? renderer.title : undefined);
    return title === UI_STRINGS.SHORTS_TITLE;
  }
"""
lite_nav = r"""  const uk6530Title =
    renderer.title?.simpleText ||
    renderer.title?.runs?.[0]?.text ||
    renderer.tabIdentifier ||
    renderer.text?.simpleText ||
    renderer.text?.runs?.[0]?.text ||
    renderer.label ||
    (typeof renderer.title === 'string' ? renderer.title : undefined);

  if (UK6530_BLOCKED_NAV_TITLES.has(normalizeUK6530NavTitle(uk6530Title))) return true;

""" + insert_point
replace_once("src/adblock.js", insert_point, lite_nav)

# 5) CSS base — sem tamanho fixo de card.
replace_once(
    "src/yt-fixes.css",
    """.ytLrWatchDefaultShadow,
[idomkey='shadow'] {
  background-image: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0) 0,
    rgba(0, 0, 0, 0.8) 90%
  ) !important;
  background-color: rgba(0, 0, 0, 0.3) !important;
}

.ytLrWatchDefault2025Shadow {
  background-color: rgba(11, 11, 11, 0.5) !important;
}
""",
    """.ytLrWatchDefaultShadow,
[idomkey='shadow'],
.ytLrWatchDefault2025Shadow {
  background: transparent !important;
  background-image: none !important;
  background-color: transparent !important;
  box-shadow: none !important;
}
"""
)

append_text("src/yt-fixes.css", r"""
/* PMCN UK6530 v3.3: layout nativo por padrão; tamanho da Início vem da
   medição real feita na aba Inscrições pela própria TV. */
html,
body,
ytlr-app {
  scroll-behavior: auto !important;
}

ytlr-tile-renderer,
ytlr-tile-renderer *,
ytlr-guide-entry-renderer,
ytlr-guide-entry-renderer *,
ytlr-tab-renderer,
ytlr-tab-renderer *,
ytlr-pivot-bar-item-renderer,
ytlr-pivot-bar-item-renderer *,
ytlr-button-renderer,
ytlr-button-renderer *,
ytlr-lockup-view-model,
ytlr-lockup-view-model *,
ytlr-navigation-item-renderer,
ytlr-navigation-item-renderer *,
yt-focus-container,
[role='menuitem'] {
  transition-property: none !important;
  transition-duration: 0s !important;
  transition-delay: 0s !important;
  scroll-behavior: auto !important;
}

html body.WEB_PAGE_TYPE_WATCH ytlr-watch-metadata[idomkey='metadata'],
html body.WEB_PAGE_TYPE_WATCH ytlr-watch-metadata,
html body.WEB_PAGE_TYPE_WATCH [idomkey='metadata'],
html body.WEB_PAGE_TYPE_WATCH .ytLrWatchDefaultShadow,
html body.WEB_PAGE_TYPE_WATCH [idomkey='shadow'],
html body.WEB_PAGE_TYPE_WATCH .ytLrWatchDefault2025Shadow {
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
}
""")

# 6) Menu lateral: DOM guard barato
menu_filter = r"""const BLOCKED = new Set([
  'jogos','games','gaming','musica','music','esportes','sports',
  'podcast','podcasts','noticias','news','filmes','movies','movies & tv',
  'ao vivo','live'
]);

function norm(value) {
  return String(value || '')
    .toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function labelOf(el) {
  return norm(el.getAttribute('aria-label') || el.getAttribute('title') || el.textContent);
}

function hideBlocked(root) {
  if (!root || (root.nodeType !== 1 && root !== document)) return;
  const selector = [
    'ytlr-guide-entry-renderer',
    'ytlr-navigation-item-renderer',
    'ytlr-pivot-bar-item-renderer',
    'ytlr-tab-renderer',
    '[role="menuitem"]',
    '[role="tab"]'
  ].join(',');

  const nodes = [];
  if (root.matches && root.matches(selector)) nodes.push(root);
  if (root.querySelectorAll) root.querySelectorAll(selector).forEach((n) => nodes.push(n));

  for (const el of nodes) {
    if (BLOCKED.has(labelOf(el))) {
      el.hidden = true;
      el.setAttribute('aria-hidden', 'true');
      el.setAttribute('tabindex', '-1');
      el.style.display = 'none';
    }
  }
}

let scheduled = false;
function schedule(root) {
  if (scheduled) return;
  scheduled = true;
  requestAnimationFrame(() => {
    scheduled = false;
    hideBlocked(root || document);
  });
}

function start() {
  hideBlocked(document);
  const host = document.querySelector('ytlr-app') || document.body || document.documentElement;
  if (!host) return;
  const observer = new MutationObserver((records) => {
    for (const record of records) {
      for (const node of record.addedNodes) {
        if (node && node.nodeType === 1) {
          schedule(node);
          return;
        }
      }
    }
  });
  observer.observe(host, { childList: true, subtree: true });
  window.addEventListener('yt-navigate-finish', () => schedule(document));
  window.addEventListener('ytaf-page-update', () => schedule(document));
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', start, { once: true });
} else {
  start();
}

export {};
"""
write_text("src/pmcn-menu-filter.js", menu_filter)

# 7) Início: neutraliza SOMENTE a expansão da prateleira em foco.\n#    Mede as fileiras recolhidas da própria aba Início e usa essa largura\n#    compacta para todas as fileiras. Sem tamanho fixo inventado.\nhome_static = r\"\"\"const STYLE_ID = 'pmcn-home-no-shelf-zoom-v1';\nconst CARD_SELECTOR = 'ytlr-tile-renderer, ytlr-lockup-view-model';\n\nfunction isHome() {\n  const href = decodeURIComponent(String(location.pathname || '') + String(location.search || '') + String(location.hash || '')).toLowerCase();\n  if (href.includes('fesubscriptions')) return false;\n  if (href.includes('fewhat_to_watch')) return true;\n  return location.hash === '' || location.hash === '#/' || location.hash === '#';\n}\n\nfunction median(values) {\n  if (!values.length) return 0;\n  const sorted = values.slice().sort((a, b) => a - b);\n  const mid = Math.floor(sorted.length / 2);\n  return sorted.length % 2 ? sorted[mid] : Math.round((sorted[mid - 1] + sorted[mid]) / 2);\n}\n\nfunction measureCollapsedWidth() {\n  if (!isHome()) return 0;\n  const rows = [];\n  document.querySelectorAll(CARD_SELECTOR).forEach((card) => {\n    const rect = card.getBoundingClientRect();\n    if (rect.bottom <= 0 || rect.top >= innerHeight) return;\n    const width = card.offsetWidth || 0;\n    if (width < 220 || width > 800) return;\n    const top = Math.round(rect.top / 24) * 24;\n    let row = rows.find((r) => Math.abs(r.top - top) <= 24);\n    if (!row) { row = { top, widths: [] }; rows.push(row); }\n    row.widths.push(width);\n  });\n  const widths = rows.filter((r) => r.widths.length >= 2).map((r) => median(r.widths)).filter((w) => w >= 220 && w <= 800);\n  return widths.length ? Math.min(...widths) : 0;\n}\n\nfunction ensureStyle(width) {\n  let style = document.getElementById(STYLE_ID);\n  if (!style) {\n    style = document.createElement('style');\n    style.id = STYLE_ID;\n    (document.head || document.documentElement).appendChild(style);\n  }\n  if (!width) {\n    style.textContent = '';\n    if (document.body) document.body.classList.remove('pmcn-home-no-shelf-zoom');\n    return;\n  }\n  style.textContent =\n    'body.pmcn-home-no-shelf-zoom ytlr-tile-renderer,' +\n    'body.pmcn-home-no-shelf-zoom ytlr-lockup-view-model {' +\n    'width:' + width + 'px !important;' +\n    'min-width:' + width + 'px !important;' +\n    'max-width:' + width + 'px !important;' +\n    'flex-basis:' + width + 'px !important;' +\n    'transform:none !important;' +\n    '}';\n  if (document.body) document.body.classList.add('pmcn-home-no-shelf-zoom');\n}\n\nlet learnedWidth = 0;\nlet timer = 0;\n\nfunction learnAndLock() {\n  if (!isHome()) { ensureStyle(0); return; }\n  if (document.body) document.body.classList.remove('pmcn-home-no-shelf-zoom');\n  const width = measureCollapsedWidth();\n  if (width) {\n    learnedWidth = width;\n    ensureStyle(width);\n    console.info('[PMCN Home] largura compacta medida:', width, 'px');\n  } else if (learnedWidth) {\n    ensureStyle(learnedWidth);\n  }\n}\n\nfunction scheduleLearn(delay = 180) {\n  clearTimeout(timer);\n  timer = setTimeout(learnAndLock, delay);\n}\n\nfunction start() {\n  scheduleLearn(250);\n  setTimeout(learnAndLock, 800);\n  setTimeout(learnAndLock, 1500);\n  window.addEventListener('hashchange', () => scheduleLearn(180));\n  window.addEventListener('popstate', () => scheduleLearn(180));\n  window.addEventListener('yt-navigate-finish', () => scheduleLearn(220));\n  window.addEventListener('ytaf-page-update', () => scheduleLearn(220));\n}\n\nif (document.readyState === 'loading') {\n  document.addEventListener('DOMContentLoaded', start, { once: true });\n} else {\n  start();\n}\n\nexport {};\n\"\"\"\nwrite_text(\"src/pmcn-home-static.js\", home_static)\n\nreplace_once(\n    \"src/userScript.js\",\n    \"import './yt-fixes.css';\\n\",\n    \"import './yt-fixes.css';\\nimport './pmcn-menu-filter.js';\\nimport './pmcn-home-static.js';\\n\"\n)\n# 8) Versionamento
appinfo_path = ROOT / "assets/appinfo.json"
appinfo = json.loads(appinfo_path.read_text(encoding="utf-8"))
appinfo["version"] = "0.8.9"
appinfo["title"] = "YouTube UK6530"
appinfo["vendor"] = "PMCN / webosbrew.org"
appinfo_path.write_text(json.dumps(appinfo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

pkg_path = ROOT / "package.json"
pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
pkg["version"] = "0.8.9"
pkg_path.write_text(json.dumps(pkg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# 9) Validação
require_contains("src/config.js", "const UK6530_LITE_PROFILE")
require_contains("src/config.js", "enableAdBlock: true")
require_contains("src/config.js", "upgradeThumbnails: false")
require_contains("src/userScript.js", "retainBehindSecs: 20")
require_contains("src/userScript.js", "import './pmcn-menu-filter.js';")
require_contains("src/userScript.js", "import './pmcn-home-static.js';")
require_contains("src/adblock.js", "normalizeUK6530NavTitle")
require_contains("src/pmcn-card-sync.js", "pmcn-subscriptions-card-width-v1")
require_contains("src/pmcn-card-sync.js", "offsetWidth")
require_contains("src/pmcn-card-sync.js", "fesubscriptions")
require_contains("src/pmcn-card-sync.js", "fewhat_to_watch")
require_contains("src/pmcn-card-sync.js", "export {};")
require_contains("assets/appinfo.json", '"version": "0.8.9"')

for needle in [
    "import './ui.js';",
    "import './sponsorblock.js';",
    "import './emoji-font.js';",
    "import './watch.js';",
]:
    require_absent("src/userScript.js", needle)

require_absent("src/adblock.js", "thumbnailHookRequired")
require_absent("src/adblock.js", "upgradeResponseThumbnails")
require_absent("src/yt-fixes.css", "width: 18rem !important")

print("PMCN UK6530 Lite v0.3.3 aplicado com sucesso.")
