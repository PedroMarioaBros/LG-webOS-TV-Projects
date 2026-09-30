const BLOCKED_LABELS = new Set([
  'shorts',
  'jogos', 'games', 'gaming',
  'musica', 'music',
  'esportes', 'sports',
  'podcast', 'podcasts',
  'noticias', 'news',
  'filmes', 'movies', 'movies & tv',
  'ao vivo', 'live'
]);

const BLOCKED_BROWSE_IDS = new Set([
  'FEshorts', 'FEshorts_tv',
  'FEgaming', 'FEgaming_destination',
  'FEmusic', 'FEmusic_home',
  'FEnews_destination',
  'FEsports_destination', 'FEsportsau',
  'FEpodcasts', 'FEpodcasts_destination',
  'FEstorefront',
  'FEtopics_live', 'FElive_destination', 'FElive_home'
]);

const GUIDE_CONTAINER_KEYS = new Set([
  'guideRenderer',
  'guideSectionRenderer',
  'guideSubscriptionsSectionRenderer',
  'tvSecondaryNavRenderer',
  'tvSecondaryNavSectionRenderer',
  'pivotBarRenderer',
  'secondaryNavRenderer'
]);

const SHORTS_ICON = 'YOUTUBE_SHORTS_FILL_24';
const SHORTS_SOURCE = 'REEL_WATCH_ENDPOINT_SOURCE_SHORTS_PIVOT_BAR';

function norm(value) {
  if (!value) return '';
  return String(value)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase();
}

function pathIsShorts(value) {
  if (typeof value !== 'string') return false;
  const path = value.split(/[?#]/, 1)[0];
  return (
    path === '/shorts' ||
    path.startsWith('/shorts/') ||
    path === '/feed/shorts' ||
    path.startsWith('/feed/shorts/') ||
    path === 'https://www.youtube.com/shorts' ||
    path.startsWith('https://www.youtube.com/shorts/') ||
    path === 'https://www.youtube.com/feed/shorts' ||
    path.startsWith('https://www.youtube.com/feed/shorts/')
  );
}

function getRenderer(entry) {
  if (!entry || typeof entry !== 'object') return null;
  return (
    entry.guideEntryRenderer ||
    entry.tabRenderer ||
    entry.pivotBarItemRenderer ||
    entry.navigationItemRenderer ||
    null
  );
}

function isBlockedGuideEntry(entry) {
  const renderer = getRenderer(entry);
  if (!renderer) return false;

  const endpoint =
    renderer.navigationEndpoint ||
    renderer.endpoint ||
    renderer.onSelectCommand ||
    renderer.command;

  const browseId =
    endpoint?.browseEndpoint?.browseId ||
    renderer.browseId ||
    renderer.pivotIdentifier ||
    renderer.tabIdentifier;

  if (browseId && BLOCKED_BROWSE_IDS.has(browseId)) return true;

  const webUrl = endpoint?.commandMetadata?.webCommandMetadata?.url;
  if (pathIsShorts(webUrl)) return true;

  const reel = endpoint?.reelWatchEndpoint;
  if (
    reel?.watchEndpointSource === SHORTS_SOURCE ||
    renderer.icon?.iconType === SHORTS_ICON
  ) {
    return true;
  }

  const title =
    renderer.title?.simpleText ||
    renderer.title?.runs?.[0]?.text ||
    renderer.formattedTitle?.simpleText ||
    renderer.formattedTitle?.runs?.[0]?.text ||
    renderer.text?.simpleText ||
    renderer.text?.runs?.[0]?.text ||
    renderer.label ||
    renderer.tabIdentifier ||
    (typeof renderer.title === 'string' ? renderer.title : '');

  return BLOCKED_LABELS.has(norm(title));
}

export function stripBlockedGuideEntries(value, depth = 0, inGuide = false) {
  if (!value || typeof value !== 'object' || depth > 24) return false;

  let changed = false;

  if (Array.isArray(value)) {
    if (inGuide) {
      for (let i = value.length - 1; i >= 0; i -= 1) {
        if (isBlockedGuideEntry(value[i])) {
          value.splice(i, 1);
          changed = true;
        }
      }
    }

    for (let i = 0; i < value.length; i += 1) {
      changed =
        stripBlockedGuideEntries(value[i], depth + 1, inGuide) || changed;
    }
    return changed;
  }

  Object.keys(value).forEach((key) => {
    const child = value[key];
    if (!child || typeof child !== 'object') return;

    const nextInGuide = inGuide || GUIDE_CONTAINER_KEYS.has(key);
    changed =
      stripBlockedGuideEntries(child, depth + 1, nextInGuide) || changed;
  });

  return changed;
}
