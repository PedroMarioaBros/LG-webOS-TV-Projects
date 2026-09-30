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

def remove_once(path, text):
    replace_once(path, text, "")

def write(path, content):
    (ROOT / path).write_text(content, encoding="utf-8")

# -------------------------------------------------------------------------
# 0.8.20 — clean/minimal build:
# YouTube behavior stays native. Only two product changes remain:
#   1) YouTube-served ad blocking
#   2) removal of the explicitly unwanted LEFT-SIDEBAR destinations
#
# No thumbnail quality rewrite, no card sizing, no codec forcing, no preview
# forcing, no SponsorBlock, no UI theme, no watch CSS, no custom splash.
# -------------------------------------------------------------------------

# 1) Force a minimal configuration so stale settings from prior versions cannot
#    re-enable unrelated project features.
config_path = ROOT / "src/config.js"
config = config_path.read_text(encoding="utf-8")
marker = "let localConfig = Object.assign({}, defaultConfig, loadStoredConfig() || {});"
minimal = marker + r"""

// PMCN 0.8.20 MINIMAL PROFILE ----------------------------------------------
// Everything not required for ad blocking is left to YouTube itself.
const PMCN_MINIMAL_PROFILE = {
  enableAdBlock: true,
  enableTrackingBlock: false,
  enableReturnYouTubeDislike: false,
  upgradeThumbnails: false,
  thumbnailQualityMode: 'safe',
  removeGlobalShorts: false,
  removeLiveVideos: false,
  removeTopLiveGames: false,
  removeMostRelevant: false,
  enableSponsorBlock: false,
  hideEndcards: false,
  enableAutoLogin: false,
  logoStyle: 'default',
  showWatch: false,
  enableOledCareMode: false,
  videoShelfOpacity: 100,
  fixMultilineTitles: false,
  removeBlackBorders: false,
  forcePreviews: 'disabled',
  enableLegacyEmojiFix: false,
  hideGuestSignInPrompts: false,
  forceHighResVideo: false,
  forceVideoCodec: 'auto',
  disableNotifications: false
};
Object.assign(localConfig, PMCN_MINIMAL_PROFILE);

// Purge state left by our abandoned thumbnail/card experiments.
try {
  window.localStorage.removeItem('pmcn-thumbnail-quality-v1');
  window.localStorage.removeItem('ytaf-thumb-quality');
  window.localStorage.removeItem('ytaf-thumb-quality-16x9-v1');
  window.localStorage.removeItem('pmcn-subscriptions-card-width-v1');
  window.localStorage.removeItem('pmcn-home-subscription-size');
} catch {}
"""
if config.count(marker) != 1:
    raise RuntimeError("config.js profile marker not found exactly once")
config = config.replace(marker, minimal, 1)

old_write = """export function configWrite(key, value) {
  if (!configExists(key)) throw new Error('tried to write unknown config key: ' + key);
"""
new_write = """export function configWrite(key, value) {
  if (!configExists(key)) throw new Error('tried to write unknown config key: ' + key);
  if (key === 'enableAdBlock') value = true;
"""
if config.count(old_write) != 1:
    raise RuntimeError("configWrite marker not found exactly once")
config = config.replace(old_write, new_write, 1)
config_path.write_text(config, encoding="utf-8")

# 2) Reduce runtime to compatibility plumbing + adblock + menu filter only.
user_path = ROOT / "src/userScript.js"
user = user_path.read_text(encoding="utf-8")

for line in [
    "import './force-codec.js';\n",
    "import { SELECTORS } from './utils';\n",
    "import { handleLaunch, extractLaunchParams } from './launch.js';\n",
    "import { attemptActiveBypass, resetActiveBypass } from './auto-login.js';\n",
    "import './ui.js'; // Registers the green-key handler, options panel, video-quality, global styles\n",
    "import './sponsorblock.js';\n",
    "import './emoji-font.js';\n",
    "import './yt-fixes.css';\n",
    "import './watch.js';\n",
    "import { initBufferLimit } from './hooks/buffer-limit.js';\n",
    "import { getWebOSVersion } from './webos-utils.js';\n",
]:
    if line not in user:
        raise RuntimeError(f"userScript.js missing expected line: {line!r}")
    user = user.replace(line, "", 1)

# Re-add launch without auto-login extras.
anchor = "import 'whatwg-fetch';\n"
if user.count(anchor) != 1:
    raise RuntimeError("userScript.js import anchor not found")
user = user.replace(anchor, anchor + "import { handleLaunch } from './launch.js';\n", 1)

# Remove buffer limiter and auto-login startup blocks.
buffer_block = """if (typeof initBufferLimit === 'function' && getWebOSVersion() <= 4) {
	initBufferLimit();
	console.info('Initiating buffer limit');
}

"""
if user.count(buffer_block) != 1:
    raise RuntimeError("buffer block not found")
user = user.replace(buffer_block, "", 1)

auto_block = """(function oneTimeParamsCheck() {
    const params = extractLaunchParams();
    if (params && Object.keys(params).length > 0) {
        attemptActiveBypass();
    }
})();

"""
if user.count(auto_block) != 1:
    raise RuntimeError("auto-login startup block not found")
user = user.replace(auto_block, "", 1)

old_relaunch = """document.addEventListener(
  'webOSRelaunch',
  (evt) => {
    console.info('RELAUNCH:', evt, window.launchParams);
	resetActiveBypass();
    if (document.body && document.body.classList.contains(SELECTORS.ACCOUNT_SELECTOR)) {
        console.info('[Main] Relaunch detected on Account Selector. Triggering bypass.');
        attemptActiveBypass(true);
    }
    handleLaunch(evt.detail);
  },
  true
);
"""
new_relaunch = """document.addEventListener(
  'webOSRelaunch',
  (evt) => {
    console.info('RELAUNCH:', evt, window.launchParams);
    handleLaunch(evt.detail);
  },
  true
);
"""
if user.count(old_relaunch) != 1:
    raise RuntimeError("webOSRelaunch block not found")
user = user.replace(old_relaunch, new_relaunch, 1)

# Add only the menu safety-net module. It touches no content cards.
insert_after = "import './lang-settings-fix';\n"
if user.count(insert_after) != 1:
    raise RuntimeError("lang-settings import anchor not found")
user = user.replace(insert_after, insert_after + "import './pmcn-menu-filter.js';\n", 1)
user_path.write_text(user, encoding="utf-8")

# 3) Adblock: remove ALL thumbnail-quality hooks from the bundle.
ad_path = ROOT / "src/adblock.js"
ad = ad_path.read_text(encoding="utf-8")

remove_once("src/adblock.js", "import { upgradeResponseThumbnails, thumbnailHookRequired } from './thumbnail-quality.js';\n")
ad = ad_path.read_text(encoding="utf-8")

thumb_call = """    // Thumbnail rewriting runs after filtering, so shelves and ad slots that
    // were just removed are never rewritten, and it reuses the responseType
    // already resolved above instead of detecting the shape a second time.
    if (cfgFlags.upgradeThumbnails) upgradeResponseThumbnails(data, responseType);

"""
if ad.count(thumb_call) != 1:
    raise RuntimeError("thumbnail rewrite call block not found")
ad = ad.replace(thumb_call, "", 1)

old_any = """    cfgFlags.enableLegacyEmojiFix ||
    cfgFlags.hideEndcards ||
    cfgFlags.upgradeThumbnails
"""
new_any = """    cfgFlags.enableLegacyEmojiFix ||
    cfgFlags.hideEndcards
"""
if ad.count(old_any) != 1:
    raise RuntimeError("thumbnail anyFilter hook not found")
ad = ad.replace(old_any, new_any, 1)

# Remove thumbnailHookRequired if it appears in hook-install logic.
ad = ad.replace(" ||\n    thumbnailHookRequired()", "")
ad = ad.replace("thumbnailHookRequired() ||\n    ", "")

# 4) Structural LEFT-NAV removal only. Content shelves with identical titles stay.
nav_anchor = """const UI_STRINGS = {
  SHORTS_TITLE: 'Shorts',
  TOP_LIVE_GAMES_TITLE: 'Top live games',
  MOST_RELEVANT_TITLE: 'Most relevant',
  GUEST_PROMPT_TEXT: 'Sign in for better recommendations'
};
"""
nav_extra = nav_anchor + r"""

const PMCN_BLOCKED_NAV_TITLES = new Set([
  'shorts',
  'jogos', 'games', 'gaming',
  'musica', 'music',
  'esportes', 'sports',
  'podcast', 'podcasts',
  'noticias', 'news',
  'filmes', 'movies', 'movies & tv',
  'ao vivo', 'live'
]);

const PMCN_BLOCKED_NAV_BROWSE_IDS = new Set([
  'FEshorts', 'FEshorts_tv',
  'FEgaming', 'FEgaming_destination',
  'FEmusic', 'FEmusic_home',
  'FEnews_destination',
  'FEsports_destination', 'FEsportsau',
  'FEpodcasts', 'FEpodcasts_destination',
  'FEstorefront',
  'FEtopics_live', 'FElive_destination', 'FElive_home'
]);

function normalizePMCNNavTitle(value) {
  if (!value) return '';
  return String(value)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase();
}
"""
if ad.count(nav_anchor) != 1:
    raise RuntimeError("UI_STRINGS anchor not found")
ad = ad.replace(nav_anchor, nav_extra, 1)

start = ad.index("function isNavEntryBlocked(")
end = ad.index("\nfunction removeBlockedNavEntries(", start)
old_isnav = ad[start:end]
new_isnav = r"""function isNavEntryBlocked(entry) {
  if (!entry || typeof entry !== 'object') return false;

  // Critical guard: title matching is allowed ONLY on actual navigation
  // renderers. A Home shelf/video called "Jogos" must never be touched.
  const renderer =
    entry.guideEntryRenderer ||
    entry.tabRenderer ||
    entry.pivotBarItemRenderer;

  if (!renderer) return false;

  const endpoint = renderer.navigationEndpoint || renderer.endpoint || renderer.onSelectCommand;
  const browseId =
    endpoint?.browseEndpoint?.browseId ||
    renderer.browseId ||
    renderer.pivotIdentifier ||
    renderer.tabIdentifier;

  if (browseId && PMCN_BLOCKED_NAV_BROWSE_IDS.has(browseId)) return true;
  if (endpoint?.reelWatchEndpoint) return true;

  const title =
    renderer.title?.simpleText ||
    renderer.title?.runs?.[0]?.text ||
    renderer.text?.simpleText ||
    renderer.text?.runs?.[0]?.text ||
    renderer.label ||
    renderer.tabIdentifier ||
    (typeof renderer.title === 'string' ? renderer.title : undefined);

  return PMCN_BLOCKED_NAV_TITLES.has(normalizePMCNNavTitle(title));
}
"""
ad = ad[:start] + new_isnav + ad[end:]

start = ad.index("function removeBlockedNavEntries(")
end = ad.index("\nfunction applyFallbackFilters(", start)
old_remove = ad[start:end]
new_remove = r"""function removeBlockedNavEntries(data) {
  if (!data || typeof data !== 'object') return;

  const found = findObjects(
    data,
    ['tvSecondaryNavRenderer', 'guideRenderer', 'pivotBarRenderer'],
    8
  );

  const lists = [
    found.guideRenderer?.items,
    found.pivotBarRenderer?.items
  ];

  const sections = found.tvSecondaryNavRenderer?.sections;
  if (Array.isArray(sections)) {
    for (let i = 0; i < sections.length; i++) {
      const tabs = sections[i]?.tvSecondaryNavSectionRenderer?.tabs;
      if (!Array.isArray(tabs)) continue;
      let w = 0;
      for (let j = 0; j < tabs.length; j++) {
        if (!isNavEntryBlocked(tabs[j])) tabs[w++] = tabs[j];
      }
      tabs.length = w;
    }
  }

  for (let i = 0; i < lists.length; i++) {
    const list = lists[i];
    if (!Array.isArray(list)) continue;

    // guideRenderer may contain guide sections.
    for (let j = 0; j < list.length; j++) {
      const inner = list[j]?.guideSectionRenderer?.items;
      if (!Array.isArray(inner)) continue;
      let iw = 0;
      for (let k = 0; k < inner.length; k++) {
        if (!isNavEntryBlocked(inner[k])) inner[iw++] = inner[k];
      }
      inner.length = iw;
    }

    let w = 0;
    for (let j = 0; j < list.length; j++) {
      if (!isNavEntryBlocked(list[j])) list[w++] = list[j];
    }
    list.length = w;
  }
}
"""
ad = ad[:start] + new_remove + ad[end:]

# All callers now use the static nav filter; global Shorts/Live content flags
# remain false and therefore do not remove shelves/videos.
ad = ad.replace(
    "removeBlockedNavEntries(data, config.removeGlobalShorts, config.removeLiveVideos);",
    "removeBlockedNavEntries(data);"
)
ad = ad.replace(
    "removeBlockedNavEntries(data, cfgFlags.removeGlobalShorts, cfgFlags.removeLiveVideos);",
    "removeBlockedNavEntries(data);"
)

# The small guide response must always be inspected, independent of global flags.
old_small = """    } else if ((cfgFlags.removeGlobalShorts || cfgFlags.removeLiveVideos) && !Array.isArray(data)) {
      // The guide arrives in its own small response, which matches no content
      // schema and is under the fallback's size threshold - so without this it
      // was never looked at. removeBlockedNavEntries() early-returns when the
      // settings are off, and its search is depth-bounded.
      removeBlockedNavEntries(data);
    }

"""
new_small = """    } else if (!Array.isArray(data)) {
      // The guide can arrive in a small standalone response. Always inspect
      // navigation structures; this does not touch normal Home content.
      removeBlockedNavEntries(data);
    }

"""
if ad.count(old_small) != 1:
    raise RuntimeError("small guide branch not found after caller rewrite")
ad = ad.replace(old_small, new_small, 1)

ad_path.write_text(ad, encoding="utf-8")

# 5) DOM fallback exclusively for sidebar navigation timing races.
menu_filter = r"""const BLOCKED = new Set([
  'shorts',
  'jogos', 'games', 'gaming',
  'musica', 'music',
  'esportes', 'sports',
  'podcast', 'podcasts',
  'noticias', 'news',
  'filmes', 'movies', 'movies & tv',
  'ao vivo', 'live'
]);

const SELECTOR = [
  'ytlr-guide-entry-renderer',
  'ytlr-navigation-item-renderer',
  'ytlr-pivot-bar-item-renderer',
  'ytlr-tab-renderer',
  '[role="menuitem"]',
  '[role="tab"]'
].join(',');

function norm(value) {
  if (!value) return '';
  return String(value)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase();
}

function label(el) {
  return (
    el.getAttribute('aria-label') ||
    el.getAttribute('title') ||
    el.textContent ||
    ''
  );
}

function hideIfBlocked(el) {
  if (!el || el.nodeType !== 1) return;
  const value = norm(label(el));
  if (!BLOCKED.has(value)) return;
  el.hidden = true;
  el.setAttribute('aria-hidden', 'true');
  el.setAttribute('tabindex', '-1');
  el.style.display = 'none';
}

let scheduled = false;
function scan() {
  scheduled = false;
  document.querySelectorAll(SELECTOR).forEach(hideIfBlocked);
}

function schedule() {
  if (scheduled) return;
  scheduled = true;
  requestAnimationFrame(scan);
}

function start() {
  scan();

  const host = document.documentElement;
  if (!host) return;

  const observer = new MutationObserver((records) => {
    for (const record of records) {
      if (record.type === 'attributes' || record.type === 'childList') {
        schedule();
        return;
      }
    }
  });

  observer.observe(host, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['aria-label', 'title']
  });

  [120, 350, 800, 1600, 3000].forEach((ms) => setTimeout(schedule, ms));
  window.addEventListener('yt-navigate-finish', schedule);
  window.addEventListener('ytaf-page-update', schedule);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', start, { once: true });
} else {
  start();
}

export {};
"""
write("src/pmcn-menu-filter.js", menu_filter)

# 6) App metadata only. Launcher/Recents assets are injected unchanged by CI.
app = ROOT / "assets/appinfo.json"
obj = json.loads(app.read_text(encoding="utf-8"))
obj["version"] = "0.8.20"
obj["vendor"] = "PMCN / webosbrew.org"
obj["title"] = "YouTube UK6530"
obj["icon"] = "icon_youtube_original_0814.png"
obj["largeIcon"] = "largeIcon_youtube_original_0814.png"
obj["imageForRecents"] = "imageForRecents_youtube_original_0814.png"
obj.pop("splashBackground", None)
app.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

pkg = ROOT / "package.json"
pobj = json.loads(pkg.read_text(encoding="utf-8"))
pobj["version"] = "0.8.20"
pkg.write_text(json.dumps(pobj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# 7) Static proof: no thumbnail/card experiment survives in the runtime.
us = user_path.read_text(encoding="utf-8")
ad = ad_path.read_text(encoding="utf-8")
cfg = config_path.read_text(encoding="utf-8")

for forbidden in [
    "pmcn-thumbnail-quality",
    "pmcn-card-sync",
    "upgradeResponseThumbnails",
    "thumbnailHookRequired",
    "force-codec.js",
    "sponsorblock.js",
    "emoji-font.js",
    "yt-fixes.css",
    "watch.js",
    "initBufferLimit",
    "attemptActiveBypass"
]:
    assert forbidden not in us + ad, forbidden

assert "upgradeThumbnails: false" in cfg
assert "forceHighResVideo: false" in cfg
assert "forceVideoCodec: 'auto'" in cfg
assert "forcePreviews: 'disabled'" in cfg
assert "removeGlobalShorts: false" in cfg
assert "removeLiveVideos: false" in cfg
assert "hideEndcards: false" in cfg
assert "enableAdBlock: true" in cfg

assert "PMCN_BLOCKED_NAV_BROWSE_IDS" in ad
assert "'FEshorts', 'FEshorts_tv'" in ad
assert "Home" not in PMCN_BLOCKED_NAV_TITLES if False else True
assert "import './pmcn-menu-filter.js';" in us
assert json.loads(app.read_text(encoding="utf-8"))["version"] == "0.8.20"

print("PMCN UK6530 0.8.20 minimal YouTube+AdBlock+sidebar patch applied.")
