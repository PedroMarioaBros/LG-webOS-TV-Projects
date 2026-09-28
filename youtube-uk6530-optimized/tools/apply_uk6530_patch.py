#!/usr/bin/env python3
"""
PMCN YouTube UK6530 v0.2.0 — build Lite agressiva para LG UK6530PSF/webOS 4.

Objetivo:
- zero anúncios servidos pelo YouTube;
- reduzir ao mínimo código/runtime opcional;
- remover módulos que o usuário não usa;
- remover atalhos/categorias de navegação não desejados antes da renderização;
- tornar transições de foco/menu instantâneas;
- manter reprodução, busca, início, inscrições, biblioteca e configurações do YouTube.

Upstream fixado pelo workflow:
NicholasBly/youtube-webos @ 5f7aa18fa0829b4e0607475222d5adacd85c6eff
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

def require_contains(path: str, needle: str) -> None:
    data = (ROOT / path).read_text(encoding="utf-8")
    if needle not in data:
        raise RuntimeError(f"{path}: validação falhou; trecho ausente: {needle}")

def require_absent(path: str, needle: str) -> None:
    data = (ROOT / path).read_text(encoding="utf-8")
    if needle in data:
        raise RuntimeError(f"{path}: validação falhou; trecho ainda presente: {needle}")

# ---------------------------------------------------------------------------
# 1) Perfil FIXO Lite: sem depender das preferências antigas do localStorage
# ---------------------------------------------------------------------------

profile_marker = "let localConfig = Object.assign({}, defaultConfig, loadStoredConfig() || {});"
profile_block = profile_marker + r"""

// PMCN UK6530 LITE v2 -------------------------------------------------------
// This build deliberately fixes the expensive/unused options instead of
// exposing a large configuration UI. Values are applied on every boot so an
// older v0.1 localStorage cannot silently re-enable background features.
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
  window.localStorage.setItem('pmcn-uk6530-profile', 'lite-v2');
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
# 2) Cortar módulos opcionais inteiros do bundle.
#    ui.js puxava settings/shortcuts/SponsorBlock UI/qualidade/logo/notificações.
# ---------------------------------------------------------------------------

for line in [
    "import './ui.js'; // Registers the green-key handler, options panel, video-quality, global styles\n",
    "import './sponsorblock.js';\n",
    "import './emoji-font.js';\n",
    "import './watch.js';\n",
]:
    remove_once("src/userScript.js", line)

# Buffer conservador-agressivo já validado em v0.1: manter 20 s.
replace_once(
    "src/userScript.js",
    "initBufferLimit();\n\tconsole.info('Initiating buffer limit');",
    "initBufferLimit({ retainBehindSecs: 20, minTrimSecs: 10, trimIntervalMs: 5000 });\n\tconsole.info('Initiating UK6530 Lite buffer limit');"
)

# ---------------------------------------------------------------------------
# 3) Remover completamente o motor de miniaturas HD do caminho do adblock.
#    Na v0.2 ele não é configurável nem carregado.
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
# 4) Navegação Lite: remover categorias que o usuário não usa ANTES do DOM.
#    Mantemos Pesquisa, Início, Inscrições, Biblioteca e Configurações.
# ---------------------------------------------------------------------------

ui_strings_end = """const UI_STRINGS = {
  SHORTS_TITLE: 'Shorts',
  TOP_LIVE_GAMES_TITLE: 'Top live games',
  MOST_RELEVANT_TITLE: 'Most relevant',
  GUEST_PROMPT_TEXT: 'Sign in for better recommendations'
};
"""
nav_block = ui_strings_end + r"""

// PMCN UK6530 Lite: category/navigation entries removed before rendering.
// Exact PT-BR and EN labels are intentional: the TV is PT-BR, while YouTube
// occasionally returns untranslated labels during experiments/account changes.
const UK6530_BLOCKED_NAV_TITLES = new Set([
  'Jogos', 'Gaming', 'Games',
  'Música', 'Music',
  'Esportes', 'Sports',
  'Podcast', 'Podcasts',
  'Notícias', 'News',
  'Filmes', 'Movies', 'Movies & TV',
  'Ao vivo', 'Live'
]);
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
    (typeof renderer.title === 'string' ? renderer.title : undefined);

  if (UK6530_BLOCKED_NAV_TITLES.has(uk6530Title)) return true;

""" + insert_point
replace_once("src/adblock.js", insert_point, lite_nav)

# ---------------------------------------------------------------------------
# 5) "Animações 0": remover transições cosméticas da navegação, sem matar
#    spinners/loading nem mexer nas animações do próprio vídeo.
# ---------------------------------------------------------------------------

append_text("src/yt-fixes.css", r"""
/* PMCN UK6530 Lite v2 -------------------------------------------------------
   Focus/menu transitions are made instantaneous. We intentionally do NOT use
   "* { animation: none }": YouTube loading spinners and player internals still
   need CSS animations. */
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
""")

# ---------------------------------------------------------------------------
# 6) Identificação/versionamento
# ---------------------------------------------------------------------------

appinfo_path = ROOT / "assets/appinfo.json"
appinfo = json.loads(appinfo_path.read_text(encoding="utf-8"))
appinfo["version"] = "0.8.5"
appinfo["title"] = "YouTube UK6530"
appinfo["vendor"] = "PMCN / webosbrew.org"
appinfo_path.write_text(json.dumps(appinfo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

pkg_path = ROOT / "package.json"
pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
pkg["version"] = "0.8.5"
pkg_path.write_text(json.dumps(pkg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# 7) Fail-fast: nunca publicar uma v0.2 parcialmente aplicada
# ---------------------------------------------------------------------------

require_contains("src/config.js", "const UK6530_LITE_PROFILE")
require_contains("src/config.js", "enableAdBlock: true")
require_contains("src/config.js", "forceVideoCodec: 'no_av1'")
require_contains("src/config.js", "forcePreviews: 'force_off'")
require_contains("src/config.js", "removeGlobalShorts: true")
require_contains("src/config.js", "removeLiveVideos: true")
require_contains("src/userScript.js", "retainBehindSecs: 20")
require_contains("src/adblock.js", "UK6530_BLOCKED_NAV_TITLES")
require_contains("src/yt-fixes.css", "PMCN UK6530 Lite v2")
require_contains("assets/appinfo.json", '"version": "0.8.5"')

for needle in [
    "import './ui.js';",
    "import './sponsorblock.js';",
    "import './emoji-font.js';",
    "import './watch.js';",
]:
    require_absent("src/userScript.js", needle)

require_absent("src/adblock.js", "thumbnailHookRequired")
require_absent("src/adblock.js", "upgradeResponseThumbnails")

print("PMCN UK6530 Lite v0.2.0 aplicado com sucesso.")
