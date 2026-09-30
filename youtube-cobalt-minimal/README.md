# YouTube UK6530 — Cobalt Minimal

This variant is intentionally minimal.

Custom behavior is limited to:
1. YouTube ad blocking.
2. Pre-render removal of selected sidebar destinations:
   Shorts, Jogos/Gaming, Música, Esportes, Podcasts, Notícias, Filmes and Ao Vivo.

Everything else is left to YouTube/Cobalt:
- thumbnails and their quality;
- card geometry and focus behavior;
- fonts, text colors and backgrounds;
- player UI and video quality;
- codec selection;
- previews;
- recommendations and shelves;
- account UI.

The build uses the Cobalt AdFree v1.2.5 release as the native runtime base and
replaces only its injected webapp layer with the minimal PMCN layer above.
