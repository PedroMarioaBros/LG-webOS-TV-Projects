// PMCN Cobalt Minimal — fixed configuration.
// The custom layer is deliberately limited to ad blocking.
// All YouTube UI, thumbnails, layout, playback and visual behavior stay native.
const FIXED = Object.freeze({
  enableAdBlock: true,
  enableSponsoredQrCodeBlock: true
});

export function configRead(key) {
  return Boolean(FIXED[key]);
}

export function configWrite() {
  // Intentionally immutable: there is no custom settings UI in the minimal build.
  return null;
}
