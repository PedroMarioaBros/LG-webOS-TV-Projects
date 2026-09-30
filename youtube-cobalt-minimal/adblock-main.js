console.info('[PMCN Cobalt Minimal] adblock main loading');

import './text-data-guard';
import './domrect-polyfill';
import './json-stringify-hook';

import { userScriptStartAdBlock } from './adblock.js';

try {
  userScriptStartAdBlock();
  console.info('[PMCN Cobalt Minimal] adblock active');
} catch (err) {
  console.error('[PMCN Cobalt Minimal] adblock failed:', err);
}
