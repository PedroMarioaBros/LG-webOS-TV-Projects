#!/usr/bin/env python3
"""
PMCN YouTube UK6530 v0.3.0 — interface compacta para LG UK6530PSF/webOS 4.

Base: perfil Lite v0.2.0.
Novidades:
- cartões compactos (~18rem) em todas as grades/prateleiras de vídeo;
- remoção robusta das categorias Jogos/Música/Esportes/Podcasts/Notícias/Filmes/Ao vivo;
- retirada dos gradientes/camadas pretas adicionados pelo fork;
- mantém thumbnails originais/leves do YouTube (sem Max Thumbnail Quality);
- preserva adblock fixo, AV1 evitado e buffer traseiro de 20 s.
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
    p = ROOT / path
    p.write_text(text, encoding="utf-8")

def require_contains(path: str, needle: str) -> None:
    data = (ROOT / path).read_text(encoding="utf-8")
    if needle not in data:
        raise RuntimeError(f"{path}: validação falhou; trecho ausente: {needle}")

def require_absent(path: str, needle: str) -> None:
    data = (ROOT / path).read_text(encoding="utf-8")
    if needle in data:
        raise RuntimeError(f"{path}: validação falhou; trecho ainda presente: {needle}")

# ---------------------------------------------------------------------------
# 1) Perfil fixo Lite
# ---------------------------------------------------------------------------

profile_marker = "let localConfig = Object.assign({}, defaultConfig, loadStoredConfig() || {});"
profile_block = profile_marker + r"""

// PMCN UK6530 LITE v3 -------------------------------------------------------
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
  window.localStorage.setItem('pmcn-uk6530-profile', 'lite-v3');
} catch {
  // Storage failure must never stop YouTube from launching.
}
"""
replace_once("src/config.js", profile_marker, profile_block)

replace_once(
    "src/config.js",
    "export function configWrite(key, value) {\n  if (!configExists(key)) throw new Error('tried to write unknown config key: ' + key);",
    "export function configWrite(key, value) {\n  if (!configExists(key)) throw new Error('tried to write unknown config key: ' + key);\n  if (key === 'enableAdBlock') value = true;"
)

# ---------------------------------------------------------------------------
# 2) Cortes do bundle Lite
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# 3) Sem motor pesado de miniaturas HD
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# 4) Filtro JSON de navegação (primeira barreira)
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# 5) CSS: zero animações cosméticas + cards compactos + sem overlay preto
# ---------------------------------------------------------------------------

# Neutraliza o gradiente/camada escura que o fork adiciona ao player.
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
/* PMCN UK6530 Lite v3 -------------------------------------------------------
   Layout compacto inspirado na aba Inscrições: preserva as miniaturas leves
   fornecidas pelo YouTube e reduz a ampliação visual que evidenciava pixelização. */
html,
body,
ytlr-app {
  scroll-behavior: auto !important;
}

ytlr-tile-renderer,
ytlr-lockup-view-model {
  width: 18rem !important;
  min-width: 18rem !important;
  max-width: 18rem !important;
  flex: 0 0 18rem !important;
}

ytlr-tile-renderer ytlr-tile-header-renderer,
ytlr-lockup-view-model ytlr-tile-header-renderer {
  width: 100% !important;
  max-width: 100% !important;
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
""")

# ---------------------------------------------------------------------------
# 6) DOM guard: segunda barreira para o menu lateral.
#    É childList-only e não mede layout, para não criar jank.
# ---------------------------------------------------------------------------

pmcn_ui = r"""const BLOCKED = new Set([
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
  if (!root || root.nodeType !== 1 && root !== document) return;
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
    const label = labelOf(el);
    if (BLOCKED.has(label)) {
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
"""
write_text("src/pmcn-compact-ui.js", pmcn_ui)

replace_once(
    "src/userScript.js",
    "import './yt-fixes.css';\n",
    "import './yt-fixes.css';\nimport './pmcn-compact-ui.js';\n"
)

# ---------------------------------------------------------------------------
# 7) Versionamento
# ---------------------------------------------------------------------------

appinfo_path = ROOT / "assets/appinfo.json"
appinfo = json.loads(appinfo_path.read_text(encoding="utf-8"))
appinfo["version"] = "0.8.6"
appinfo["title"] = "YouTube UK6530"
appinfo["vendor"] = "PMCN / webosbrew.org"
appinfo_path.write_text(json.dumps(appinfo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

pkg_path = ROOT / "package.json"
pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
pkg["version"] = "0.8.6"
pkg_path.write_text(json.dumps(pkg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# 8) Fail-fast
# ---------------------------------------------------------------------------

require_contains("src/config.js", "const UK6530_LITE_PROFILE")
require_contains("src/config.js", "enableAdBlock: true")
require_contains("src/config.js", "forceVideoCodec: 'no_av1'")
require_contains("src/config.js", "upgradeThumbnails: false")
require_contains("src/userScript.js", "retainBehindSecs: 20")
require_contains("src/userScript.js", "import './pmcn-compact-ui.js';")
require_contains("src/adblock.js", "normalizeUK6530NavTitle")
require_contains("src/yt-fixes.css", "PMCN UK6530 Lite v3")
require_contains("src/yt-fixes.css", "width: 18rem !important")
require_contains("src/yt-fixes.css", "background: transparent !important")
require_contains("assets/appinfo.json", '"version": "0.8.6"')

for needle in [
    "import './ui.js';",
    "import './sponsorblock.js';",
    "import './emoji-font.js';",
    "import './watch.js';",
]:
    require_absent("src/userScript.js", needle)

require_absent("src/adblock.js", "thumbnailHookRequired")
require_absent("src/adblock.js", "upgradeResponseThumbnails")

print("PMCN UK6530 Lite v0.3.0 aplicado com sucesso.")
