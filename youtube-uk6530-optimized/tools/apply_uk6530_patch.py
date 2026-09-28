#!/usr/bin/env python3
"""
Aplica o perfil PMCN UK6530 sobre o upstream NicholasBly/youtube-webos.

Objetivos desta primeira versão:
- manter o bloqueio de anúncios sempre ligado;
- reduzir trabalho em segundo plano;
- evitar AV1 na LG UK6530PSF;
- reduzir retenção de buffer para aliviar pressão de memória no webOS 4;
- desligar por padrão recursos opcionais mais pesados;
- remover completamente o runtime do Return YouTube Dislike nesta variante.

O script falha se o upstream mudar de forma incompatível, para evitar gerar
silenciosamente um pacote parcialmente modificado.
"""

from pathlib import Path
import json

ROOT = Path.cwd()

def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    data = p.read_text(encoding="utf-8")
    count = data.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: esperado 1 trecho para substituir, encontrado {count}")
    p.write_text(data.replace(old, new, 1), encoding="utf-8")

def require_contains(path: str, needle: str) -> None:
    data = (ROOT / path).read_text(encoding="utf-8")
    if needle not in data:
        raise RuntimeError(f"{path}: validação falhou; trecho ausente: {needle}")

# ---------------------------------------------------------------------------
# 1) Perfil de configuração leve para a UK6530
# ---------------------------------------------------------------------------

replace_once(
    "src/config.js",
    "['enableTrackingBlock', { default: false, desc: 'Reduce Telemetry & Tracking' }],",
    "['enableTrackingBlock', { default: true, desc: 'Reduce Telemetry & Tracking' }],"
)
replace_once(
    "src/config.js",
    "['enableReturnYouTubeDislike', { default: true, desc: 'Return YouTube Dislike' }],",
    "['enableReturnYouTubeDislike', { default: false, desc: 'Return YouTube Dislike' }],"
)
replace_once(
    "src/config.js",
    "['enableSponsorBlock', { default: true, desc: 'SponsorBlock' }],",
    "['enableSponsorBlock', { default: false, desc: 'SponsorBlock' }],"
)
replace_once(
    "src/config.js",
    "['enableLegacyEmojiFix', { default: true, desc: 'Emoji + Characters Fix' }],",
    "['enableLegacyEmojiFix', { default: false, desc: 'Emoji + Characters Fix' }],"
)
replace_once(
    "src/config.js",
    "['forceVideoCodec', { default: 'auto', desc: 'Force Video Codec' }],",
    "['forceVideoCodec', { default: 'no_av1', desc: 'Force Video Codec' }],"
)

profile_marker = "let localConfig = Object.assign({}, defaultConfig, loadStoredConfig() || {});"
profile_block = profile_marker + r"""

// PMCN UK6530 profile -------------------------------------------------------
// Apply once even when this package replaces an older YouTube AdFree build.
// Afterwards the user may change optional features normally. Ad blocking is
// the sole setting intentionally locked on for this TV-specific variant.
const UK6530_PROFILE_KEY = 'pmcn-uk6530-profile-v1';
const UK6530_FIRST_RUN_PROFILE = {
  enableAdBlock: true,
  enableTrackingBlock: true,
  enableReturnYouTubeDislike: false,
  upgradeThumbnails: false,
  enableSponsorBlock: false,
  showWatch: false,
  forceHighResVideo: false,
  forceVideoCodec: 'no_av1',
  enableLegacyEmojiFix: false,
  forcePreviews: 'disabled'
};

try {
  if (window.localStorage.getItem(UK6530_PROFILE_KEY) !== '1') {
    Object.assign(localConfig, UK6530_FIRST_RUN_PROFILE);
    window.localStorage.setItem(CONFIG_KEY, JSON.stringify(localConfig));
    window.localStorage.setItem(UK6530_PROFILE_KEY, '1');
  }
} catch {
  // Storage failure must never stop YouTube from launching.
}

// This variant is explicitly an ad-free build.
localConfig.enableAdBlock = true;
"""
replace_once("src/config.js", profile_marker, profile_block)

replace_once(
    "src/config.js",
    "export function configWrite(key, value) {\n  if (!configExists(key)) throw new Error('tried to write unknown config key: ' + key);",
    "export function configWrite(key, value) {\n  if (!configExists(key)) throw new Error('tried to write unknown config key: ' + key);\n  if (key === 'enableAdBlock') value = true;"
)

# ---------------------------------------------------------------------------
# 2) Menos pressão de memória: buffer traseiro de 20 s no webOS <= 4
# ---------------------------------------------------------------------------

replace_once(
    "src/userScript.js",
    "initBufferLimit();\n\tconsole.info('Initiating buffer limit');",
    "initBufferLimit({ retainBehindSecs: 20, minTrimSecs: 10, trimIntervalMs: 5000 });\n\tconsole.info('Initiating UK6530 buffer limit');"
)

# ---------------------------------------------------------------------------
# 3) Retirar runtime pesado do Return YouTube Dislike
#    Quando desativado no upstream ele ainda instala navegação/observers.
# ---------------------------------------------------------------------------

replace_once(
    "src/ui.js",
    "import './return-dislike.js';\n",
    ""
)

replace_once(
    "src/ui.js",
    "  createVideoCodecControl(),\n  createConfigCheckbox('hideEndcards'),\n  createConfigCheckbox('enableReturnYouTubeDislike')]))",
    "  createVideoCodecControl(),\n  createConfigCheckbox('hideEndcards')]))"
)

# ---------------------------------------------------------------------------
# 4) Identificação do pacote de teste
# ---------------------------------------------------------------------------

appinfo_path = ROOT / "assets/appinfo.json"
appinfo = json.loads(appinfo_path.read_text(encoding="utf-8"))
appinfo["version"] = "0.8.4"
appinfo["title"] = "YouTube UK6530"
appinfo["vendor"] = "PMCN / webosbrew.org"
appinfo_path.write_text(json.dumps(appinfo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

pkg_path = ROOT / "package.json"
pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
pkg["version"] = "0.8.4"
pkg_path.write_text(json.dumps(pkg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# 5) Validações que tornam a build fail-fast
# ---------------------------------------------------------------------------

require_contains("src/config.js", "localConfig.enableAdBlock = true;")
require_contains("src/config.js", "if (key === 'enableAdBlock') value = true;")
require_contains("src/config.js", "default: 'no_av1'")
require_contains("src/userScript.js", "retainBehindSecs: 20")
require_contains("assets/appinfo.json", '"title": "YouTube UK6530"')

ui = (ROOT / "src/ui.js").read_text(encoding="utf-8")
if "import './return-dislike.js';" in ui:
    raise RuntimeError("Return YouTube Dislike ainda está importado")

print("Perfil UK6530 aplicado com sucesso.")
