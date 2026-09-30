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

# 1) Remove the old broad title filter from generic renderers.
# It could act outside navigation; the new structural filter below is nav-only.
old_generic = """  const uk6530Title =
    renderer.title?.simpleText ||
    renderer.title?.runs?.[0]?.text ||
    renderer.tabIdentifier ||
    renderer.text?.simpleText ||
    renderer.text?.runs?.[0]?.text ||
    renderer.label ||
    (typeof renderer.title === 'string' ? renderer.title : undefined);

  if (UK6530_BLOCKED_NAV_TITLES.has(normalizeUK6530NavTitle(uk6530Title))) return true;

"""
replace_once("src/adblock.js", old_generic, "")

# 2) Add concrete browse IDs for the unwanted LEFT NAV destinations.
old_set = """const UK6530_BLOCKED_NAV_TITLES = new Set([
  'jogos', 'games', 'gaming',
  'musica', 'music',
  'esportes', 'sports',
  'podcast', 'podcasts',
  'noticias', 'news',
  'filmes', 'movies', 'movies & tv',
  'ao vivo', 'live'
]);
"""
new_set = old_set + """
const UK6530_BLOCKED_NAV_BROWSE_IDS = new Set([
  'FEgaming', 'FEgaming_destination',
  'FEmusic', 'FEmusic_home',
  'FEnews_destination',
  'FEsports_destination', 'FEsportsau',
  'FEpodcasts', 'FEpodcasts_destination',
  'FEstorefront',
  'FEtopics_live', 'FElive_destination', 'FElive_home'
]);
"""
replace_once("src/adblock.js", old_set, new_set)

# 3) Make removal structural: only guide / secondary-nav / pivot entries are dropped.
old_nav = """function isNavEntryBlocked(entry, removeGlobalShorts, removeLiveVideos) {
  if (!entry || typeof entry !== 'object') return false;

  const renderer =
    entry.guideEntryRenderer ||
    entry.tabRenderer ||
    entry.pivotBarItemRenderer ||
    entry;

  const endpoint = renderer.navigationEndpoint || renderer.endpoint || renderer.onSelectCommand;
  if (endpoint) {
    if (removeGlobalShorts && endpoint.reelWatchEndpoint) return true;
    const browseId = endpoint.browseEndpoint?.browseId;
    if (removeGlobalShorts && (browseId === 'FEshorts' || browseId === 'FEshorts_tv')) return true;
    if (removeLiveVideos && browseId === 'FEtopics_live') return true;
  }

  if (removeGlobalShorts) {
    const title =
      renderer.title?.simpleText ||
      renderer.title?.runs?.[0]?.text ||
      renderer.tabIdentifier ||
      (typeof renderer.title === 'string' ? renderer.title : undefined);
    return title === UI_STRINGS.SHORTS_TITLE;
  }
  return false;
}
"""
new_nav = """function isNavEntryBlocked(entry, removeGlobalShorts, removeLiveVideos) {
  if (!entry || typeof entry !== 'object') return false;

  const renderer =
    entry.guideEntryRenderer ||
    entry.tabRenderer ||
    entry.pivotBarItemRenderer ||
    entry;

  const endpoint = renderer.navigationEndpoint || renderer.endpoint || renderer.onSelectCommand;
  const browseId =
    endpoint?.browseEndpoint?.browseId ||
    renderer.browseId ||
    renderer.pivotIdentifier ||
    renderer.tabIdentifier;

  if (endpoint && removeGlobalShorts && endpoint.reelWatchEndpoint) return true;
  if (removeGlobalShorts && (browseId === 'FEshorts' || browseId === 'FEshorts_tv')) return true;
  if (removeLiveVideos && browseId === 'FEtopics_live') return true;

  // PMCN UK6530: delete unwanted destinations BEFORE the navigation UI is rendered.
  // This intentionally runs only on nav entries, so a Home shelf titled "Jogos"
  // remains normal content and is not removed.
  if (browseId && UK6530_BLOCKED_NAV_BROWSE_IDS.has(browseId)) return true;

  const title =
    renderer.title?.simpleText ||
    renderer.title?.runs?.[0]?.text ||
    renderer.text?.simpleText ||
    renderer.text?.runs?.[0]?.text ||
    renderer.label ||
    renderer.tabIdentifier ||
    (typeof renderer.title === 'string' ? renderer.title : undefined);

  if (UK6530_BLOCKED_NAV_TITLES.has(normalizeUK6530NavTitle(title))) return true;
  if (removeGlobalShorts && title === UI_STRINGS.SHORTS_TITLE) return true;
  return false;
}
"""
replace_once("src/adblock.js", old_nav, new_nav)

# 4) Strengthen the DOM fallback without making it the primary mechanism.
# It now catches text-node insertion and late aria-label/title hydration,
# and does several cheap, finite startup rescans.
menu = ROOT / "src/pmcn-menu-filter.js"
data = menu.read_text(encoding="utf-8")
old_mut = """  const observer = new MutationObserver((records) => {
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
"""
new_mut = """  const observer = new MutationObserver((records) => {
    for (const record of records) {
      if (record.type === 'attributes' || (record.addedNodes && record.addedNodes.length)) {
        // Full menu rescan is cheap (very few matching nav nodes) and avoids
        // missing labels inserted as text nodes after the element already exists.
        schedule(document);
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

  // Finite startup retries eliminate the first-load race without a polling loop.
  [120, 350, 800, 1600, 3000].forEach((ms) => setTimeout(() => schedule(document), ms));

  window.addEventListener('yt-navigate-finish', () => schedule(document));
  window.addEventListener('ytaf-page-update', () => schedule(document));
"""
if data.count(old_mut) != 1:
    raise RuntimeError("pmcn-menu-filter.js: startup observer block not found exactly once")
menu.write_text(data.replace(old_mut, new_mut, 1), encoding="utf-8")

# 5) Version only. Assets are generated later in the workflow.
app = ROOT / "assets/appinfo.json"
obj = json.loads(app.read_text(encoding="utf-8"))
obj["version"] = "0.8.14"
app.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

pkg = ROOT / "package.json"
pobj = json.loads(pkg.read_text(encoding="utf-8"))
pobj["version"] = "0.8.14"
pkg.write_text(json.dumps(pobj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Validation
ad = (ROOT / "src/adblock.js").read_text(encoding="utf-8")
mf = menu.read_text(encoding="utf-8")
assert "UK6530_BLOCKED_NAV_BROWSE_IDS" in ad
assert "FEpodcasts_destination" in ad
assert "FEstorefront" in ad
assert "FEgaming_destination" in ad
assert "Home shelf titled \"Jogos\"" in ad
assert "attributeFilter: ['aria-label', 'title']" in mf
assert "3000" in mf
assert old_generic not in ad
assert json.loads(app.read_text(encoding="utf-8"))["version"] == "0.8.14"
print("PMCN UK6530 0.8.14 delta applied successfully.")
