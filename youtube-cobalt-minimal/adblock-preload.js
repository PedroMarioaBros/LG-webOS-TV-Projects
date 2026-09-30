import { stripBlockedGuideEntries } from './pmcn-nav-filter.mjs';

if (!window.__pmcnMinimalPreloadInstalled) {
  window.__pmcnMinimalPreloadInstalled = true;

  const descriptor = Object.getOwnPropertyDescriptor(JSON, 'parse');
  const nativeParse = JSON.parse;
  let downstreamParse = nativeParse;
  let parsing = false;

  function pmcnParse() {
    if (parsing) {
      return nativeParse.apply(this, arguments);
    }

    parsing = true;
    try {
      const value = downstreamParse.apply(this, arguments);
      if (stripBlockedGuideEntries(value)) {
        console.info('[PMCN Cobalt Minimal] blocked sidebar entries removed');
      }
      return value;
    } finally {
      parsing = false;
    }
  }

  if (!descriptor || descriptor.configurable) {
    Object.defineProperty(JSON, 'parse', {
      configurable: true,
      enumerable: descriptor ? descriptor.enumerable : false,
      get() {
        return pmcnParse;
      },
      set(parser) {
        if (typeof parser === 'function' && parser !== pmcnParse) {
          downstreamParse = parser;
        }
      }
    });
  } else {
    JSON.parse = pmcnParse;
  }

  console.info('[PMCN Cobalt Minimal] preload installed');
}
