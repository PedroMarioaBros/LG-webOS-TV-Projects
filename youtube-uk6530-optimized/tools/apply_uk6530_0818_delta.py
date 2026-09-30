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

css = r"""
/* PMCN UK6530 0.8.18 — exact opaque-text layer cleanup.
   0.8.17 reached the visible text elements but missed the stronger parent /
   pseudo-element layers used by YouTube TV. Remove those layers and force the
   actual glyphs back to pure white. */

/* Strong opaque layers identified in the original YouTube-TV UI rules. */
.app-quality-root .boSXqb .QFqCxd,
.app-quality-root .boSXqb .QFqCxd::before,
.app-quality-root .boSXqb .QFqCxd::after,
.app-quality-root .V7jTHe,
.app-quality-root .V7jTHe::before,
.app-quality-root .V7jTHe::after,
.app-quality-root .g6XRz,
.app-quality-root .g6XRz::before,
.app-quality-root .g6XRz::after,
.app-quality-root .UGcxnc .sjENQb,
.app-quality-root .UGcxnc .sjENQb::before,
.app-quality-root .UGcxnc .sjENQb::after {
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
}

/* Title / metadata / timecodes: white letters, no local black box. */
yt-formatted-string.XGffTd.WVWtef,
yt-formatted-string.XGffTd.y98TDb,
span[idomkey^='detail-text-'],
span.g6XRz,
span.V7jTHe {
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
  opacity: 1 !important;
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
  text-shadow: 0 1px 4px rgba(0,0,0,.85) !important;
}

/* Pseudo-elements carrying separators must not recreate black rectangles. */
yt-formatted-string.XGffTd.WVWtef::before,
yt-formatted-string.XGffTd.WVWtef::after,
yt-formatted-string.XGffTd.y98TDb::before,
yt-formatted-string.XGffTd.y98TDb::after,
span[idomkey^='detail-text-']::before,
span[idomkey^='detail-text-']::after {
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
  opacity: 1 !important;
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
}

/* Recommendation text beneath the active video. */
yt-formatted-string.XGffTd.dxLAmd,
yt-formatted-string.XGffTd.JkDfAc,
span.KzcwEe.h14Bce {
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
  opacity: 1 !important;
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
  text-shadow: 0 1px 4px rgba(0,0,0,.85) !important;
}
"""
append_once("src/yt-fixes.css", "PMCN UK6530 0.8.18 — exact opaque-text layer cleanup.", css)

app = ROOT / "assets/appinfo.json"
obj = json.loads(app.read_text(encoding="utf-8"))
obj["version"] = "0.8.18"
app.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

pkg = ROOT / "package.json"
pobj = json.loads(pkg.read_text(encoding="utf-8"))
pobj["version"] = "0.8.18"
pkg.write_text(json.dumps(pobj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

yt = (ROOT / "src/yt-fixes.css").read_text(encoding="utf-8")
for needle in [
  ".app-quality-root .boSXqb .QFqCxd::before",
  ".app-quality-root .UGcxnc .sjENQb",
  "-webkit-text-fill-color: #fff !important",
  "PMCN UK6530 0.8.18 — exact opaque-text layer cleanup."
]:
    assert needle in yt
assert json.loads(app.read_text(encoding="utf-8"))["version"] == "0.8.18"
print("PMCN UK6530 0.8.18 exact text-layer cleanup applied.")
