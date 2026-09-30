(function () {
  'use strict';

  if (window.__pmcnMinimalCobaltMain) return;
  window.__pmcnMinimalCobaltMain = true;

  var BLOCKED = {
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

  var MENU_SELECTOR = [
    'ytlr-guide-entry-renderer',
    'ytlr-navigation-item-renderer',
    'ytlr-pivot-bar-item-renderer',
    '[role="menuitem"]'
  ].join(',');

  var AD_SELECTOR = [
    'ytlr-ad-slot-renderer',
    'ytd-ad-slot-renderer',
    '.ytlr-ad-slot-renderer',
    '.ytd-ad-slot-renderer',
    '[class*="ad-slot-renderer"]'
  ].join(',');

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

  function removeNode(node) {
    if (node && node.parentNode) node.parentNode.removeChild(node);
  }

  function cleanMenu() {
    var nodes = document.querySelectorAll(MENU_SELECTOR);
    for (var i = nodes.length - 1; i >= 0; i -= 1) {
      var node = nodes[i];
      var label =
        node.getAttribute('aria-label') ||
        node.getAttribute('title') ||
        node.textContent ||
        '';
      if (BLOCKED[normalizeTitle(label)]) removeNode(node);
    }
  }

  function cleanAds(root) {
    var scope = root && root.querySelectorAll ? root : document;
    var ads = scope.querySelectorAll(AD_SELECTOR);
    for (var i = ads.length - 1; i >= 0; i -= 1) {
      var node = ads[i];
      var tile = node;
      var depth = 0;

      while (tile && tile.parentElement && tile.parentElement !== document.body && depth < 8) {
        var parent = tile.parentElement;
        if (parent.children && parent.children.length > 1) break;
        tile = parent;
        depth += 1;
      }

      removeNode(tile || node);
    }
  }

  var scheduled = false;
  function scan() {
    scheduled = false;
    cleanMenu();
    cleanAds(document);
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    if (window.requestAnimationFrame) {
      window.requestAnimationFrame(scan);
    } else {
      setTimeout(scan, 0);
    }
  }

  function start() {
    scan();

    if (!document.documentElement || !window.MutationObserver) return;

    var observer = new MutationObserver(function (records) {
      for (var i = 0; i < records.length; i += 1) {
        if (records[i].type === 'childList' || records[i].type === 'attributes') {
          schedule();
          return;
        }
      }
    });

    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['aria-label', 'title']
    });

    setTimeout(schedule, 150);
    setTimeout(schedule, 500);
    setTimeout(schedule, 1200);
    setTimeout(schedule, 2500);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, false);
  } else {
    start();
  }

  console.info('[PMCN] Minimal Cobalt main: no UI/theme/thumbnail hooks loaded');
})();