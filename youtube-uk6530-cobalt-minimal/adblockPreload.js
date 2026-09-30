(function () {
  'use strict';

  if (window.__pmcnMinimalCobaltPreload) return;
  window.__pmcnMinimalCobaltPreload = true;

  var nativeParse = JSON.parse;
  var descriptor = Object.getOwnPropertyDescriptor(JSON, 'parse');
  var downstreamParse = nativeParse;
  var parsing = false;

  var BLOCKED_IDS = {
    FEshorts: true,
    FEshorts_tv: true,
    FEgaming: true,
    FEgaming_destination: true,
    FEmusic: true,
    FEmusic_home: true,
    FEnews_destination: true,
    FEsports_destination: true,
    FEsportsau: true,
    FEpodcasts: true,
    FEpodcasts_destination: true,
    FEstorefront: true,
    FEtopics_live: true,
    FElive_destination: true,
    FElive_home: true
  };

  var BLOCKED_TITLES = {
    shorts: true,
    jogos: true,
    games: true,
    gaming: true,
    musica: true,
    music: true,
    esportes: true,
    sports: true,
    podcast: true,
    podcasts: true,
    noticias: true,
    news: true,
    filmes: true,
    movies: true,
    'movies & tv': true,
    'ao vivo': true,
    live: true
  };

  var AD_KEYS = {
    adBreakHeartbeatParams: true,
    adBreakParams: true,
    adPlacements: true,
    adSlots: true,
    adSignalsInfo: true,
    adVideoId: true,
    playerAds: true
  };

  function normalizeTitle(value) {
    return String(value || '')
      .toLowerCase()
      .replace(/[áàãâä]/g, 'a')
      .replace(/[éèêë]/g, 'e')
      .replace(/[íìîï]/g, 'i')
      .replace(/[óòõôö]/g, 'o')
      .replace(/[úùûü]/g, 'u')
      .replace(/ç/g, 'c')
      .replace(/^\s+|\s+$/g, '');
  }

  function textValue(value) {
    if (!value) return '';
    if (typeof value === 'string') return value;
    if (typeof value.simpleText === 'string') return value.simpleText;
    if (value.runs && value.runs.length && typeof value.runs[0].text === 'string') {
      return value.runs[0].text;
    }
    return '';
  }

  function endpointFrom(renderer) {
    if (!renderer || typeof renderer !== 'object') return null;
    return renderer.navigationEndpoint ||
      renderer.endpoint ||
      renderer.onSelectCommand ||
      renderer.command ||
      null;
  }

  function isShortsEndpoint(endpoint) {
    if (!endpoint || typeof endpoint !== 'object') return false;

    var browseId = endpoint.browseEndpoint && endpoint.browseEndpoint.browseId;
    if (browseId === 'FEshorts' || browseId === 'FEshorts_tv') return true;

    if (endpoint.reelWatchEndpoint) return true;

    var metadata = endpoint.commandMetadata && endpoint.commandMetadata.webCommandMetadata;
    var url = metadata && metadata.url;
    if (typeof url === 'string') {
      var path = url.split(/[?#]/, 1)[0];
      if (path === '/shorts' || path.indexOf('/shorts/') === 0 ||
          path === '/feed/shorts' || path.indexOf('/feed/shorts/') === 0) {
        return true;
      }
    }

    return false;
  }

  function isBlockedNavEntry(entry) {
    if (!entry || typeof entry !== 'object') return false;

    var renderer =
      entry.guideEntryRenderer ||
      entry.navigationItemRenderer ||
      entry.pivotBarItemRenderer ||
      entry.compactLinkRenderer;

    if (!renderer) return false;

    var endpoint = endpointFrom(renderer);
    if (isShortsEndpoint(endpoint)) return true;

    var browseId =
      (endpoint && endpoint.browseEndpoint && endpoint.browseEndpoint.browseId) ||
      renderer.browseId ||
      renderer.pivotIdentifier ||
      renderer.tabIdentifier;

    if (browseId && BLOCKED_IDS[browseId]) return true;

    var iconType =
      (renderer.icon && renderer.icon.iconType) ||
      (renderer.thumbnail && renderer.thumbnail.iconType);
    if (iconType === 'YOUTUBE_SHORTS_FILL_24') return true;

    var title = textValue(renderer.title) ||
      textValue(renderer.text) ||
      renderer.label ||
      renderer.tabIdentifier ||
      '';

    return !!BLOCKED_TITLES[normalizeTitle(title)];
  }

  function stripBlockedGuideEntries(value, depth) {
    if (!value || typeof value !== 'object' || depth > 32) return false;

    var changed = false;
    var i;
    var key;

    if (Array.isArray(value)) {
      for (i = value.length - 1; i >= 0; i -= 1) {
        if (isBlockedNavEntry(value[i])) {
          value.splice(i, 1);
          changed = true;
        } else if (stripBlockedGuideEntries(value[i], depth + 1)) {
          changed = true;
        }
      }
      return changed;
    }

    for (key in value) {
      if (!Object.prototype.hasOwnProperty.call(value, key)) continue;
      if (stripBlockedGuideEntries(value[key], depth + 1)) changed = true;
    }

    return changed;
  }

  function isAdEntry(value) {
    if (!value || typeof value !== 'object') return false;

    if (value.adSlotRenderer || value.tvMastheadRenderer) return true;

    var endpoints = [
      value.command && value.command.reelWatchEndpoint,
      value.onSelectCommand && value.onSelectCommand.reelWatchEndpoint,
      value.navigationEndpoint && value.navigationEndpoint.reelWatchEndpoint,
      value.reelItemRenderer &&
        value.reelItemRenderer.navigationEndpoint &&
        value.reelItemRenderer.navigationEndpoint.reelWatchEndpoint,
      value.tileRenderer &&
        value.tileRenderer.onSelectCommand &&
        value.tileRenderer.onSelectCommand.reelWatchEndpoint
    ];

    for (var i = 0; i < endpoints.length; i += 1) {
      var endpoint = endpoints[i];
      if (!endpoint) continue;
      var isAd = endpoint.adClientParams && endpoint.adClientParams.isAd;
      if (isAd === true || isAd === 'true' || endpoint.videoType === 'REEL_VIDEO_TYPE_AD') {
        return true;
      }
    }

    return false;
  }

  function stripAds(value, depth) {
    if (!value || typeof value !== 'object' || depth > 32) return false;

    var changed = false;
    var i;
    var key;

    if (Array.isArray(value)) {
      for (i = value.length - 1; i >= 0; i -= 1) {
        if (isAdEntry(value[i])) {
          value.splice(i, 1);
          changed = true;
        } else if (stripAds(value[i], depth + 1)) {
          changed = true;
        }
      }
      return changed;
    }

    for (key in value) {
      if (!Object.prototype.hasOwnProperty.call(value, key)) continue;

      if (AD_KEYS[key]) {
        delete value[key];
        changed = true;
        continue;
      }

      if (key === 'adSlotRenderer' || key === 'tvMastheadRenderer') {
        delete value[key];
        changed = true;
        continue;
      }

      if (stripAds(value[key], depth + 1)) changed = true;
    }

    return changed;
  }

  function pmcnParse() {
    if (parsing) return nativeParse.apply(this, arguments);

    parsing = true;
    try {
      var value = downstreamParse.apply(this, arguments);
      stripAds(value, 0);
      stripBlockedGuideEntries(value, 0);
      return value;
    } finally {
      parsing = false;
    }
  }

  if (!descriptor || descriptor.configurable) {
    Object.defineProperty(JSON, 'parse', {
      configurable: true,
      enumerable: descriptor ? descriptor.enumerable : false,
      get: function () {
        return pmcnParse;
      },
      set: function (parser) {
        if (typeof parser === 'function' && parser !== pmcnParse) {
          downstreamParse = parser;
        }
      }
    });
  } else {
    JSON.parse = pmcnParse;
  }

  console.info('[PMCN] Minimal Cobalt preload: adblock + sidebar filter active');
})();