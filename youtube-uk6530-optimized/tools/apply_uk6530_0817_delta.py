#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path.cwd()

def append_once(path, marker, block):
    p = ROOT / path
    data = p.read_text(encoding="utf-8")
    if marker in data:
        raise RuntimeError(f"{path}: marker already present")
    p.write_text(data.rstrip() + "\n\n" + block.strip() + "\n", encoding="utf-8")

# -------------------------------------------------------------------------
# 0.8.17 — remove ONLY the opaque black backgrounds immediately behind text
# on the watch screen. No navigation, thumbnails, icons, layout or player
# behavior is modified.
# -------------------------------------------------------------------------

css = r"""
/* PMCN UK6530 0.8.17 — Watch text background cleanup.
   Narrow selectors only: title, metadata, timecodes and recommendation text.
   Preserve readability with text-shadow; do not touch the player's large
   background gradient, controls, cards, navigation or video surface. */

:where(
  yt-formatted-string.XGffTd.WVWtef,
  yt-formatted-string.XGffTd.y98TDb,
  yt-formatted-string.XGffTd.y98TDb::before,
  yt-formatted-string.XGffTd.y98TDb::after,
  span.g6XRz,
  span.V7jTHe
) {
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
  text-shadow: rgba(0, 0, 0, 0.8) 0 1.25px 5px !important;
}

span[idomkey^='detail-text-'],
span[idomkey^='detail-text-']::before,
span[idomkey^='detail-text-']::after,
yt-formatted-string.XGffTd.y98TDb::before,
yt-formatted-string.XGffTd.y98TDb::after {
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
  text-shadow: rgba(0, 0, 0, 0.8) 0 1.25px 5px !important;
}

/* Recommendation tray below the active video: text and duration badge only. */
yt-formatted-string.XGffTd.dxLAmd,
yt-formatted-string.XGffTd.JkDfAc,
span.KzcwEe.h14Bce {
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
  text-shadow: rgba(0, 0, 0, 0.8) 0 1.25px 5px !important;
}
"""
append_once("src/yt-fixes.css", "PMCN UK6530 0.8.17 — Watch text background cleanup.", css)

app = ROOT / "assets/appinfo.json"
obj = json.loads(app.read_text(encoding="utf-8"))
obj["version"] = "0.8.17"
app.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

pkg = ROOT / "package.json"
pobj = json.loads(pkg.read_text(encoding="utf-8"))
pobj["version"] = "0.8.17"
pkg.write_text(json.dumps(pobj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Scope validation.
yt = (ROOT / "src/yt-fixes.css").read_text(encoding="utf-8")
assert "PMCN UK6530 0.8.17 — Watch text background cleanup." in yt
for selector in [
    "yt-formatted-string.XGffTd.WVWtef",
    "span[idomkey^='detail-text-']",
    "span.g6XRz",
    "span.V7jTHe",
    "yt-formatted-string.XGffTd.dxLAmd",
    "span.KzcwEe.h14Bce"
]:
    assert selector in yt
assert json.loads(app.read_text(encoding="utf-8"))["version"] == "0.8.17"

print("PMCN UK6530 0.8.17 narrow watch-text CSS applied.")
