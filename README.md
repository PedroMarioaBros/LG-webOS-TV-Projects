# LG webOS TV Projects

Repositório para projetos, otimizações e aplicativos personalizados para a TV **LG UK6530PSF**.

## Dispositivo-alvo

- Modelo: LG webOS TV UK6530PSF
- Geração: 2018
- webOS: família webOS 4.x
- Firmware observado: 05.50.70
- Acesso disponível: Developer Mode

## Projetos

### youtube-uk6530-optimized

Variante do YouTube AdFree para webOS com foco em:

- bloqueio de anúncios;
- estabilidade em hardware webOS antigo;
- menor consumo de memória;
- redução de processamento em segundo plano;
- compatibilidade com o player da LG UK6530PSF;
- perfil de codec conservador, evitando AV1;
- manutenção de conta, histórico, inscrições, busca e reprodução normal.

Base técnica inicial: projeto open-source `youtube-webos`, com referência ao fork otimizado `NicholasBly/youtube-webos`.

## Princípio do projeto

Primeiro estabilidade e fluidez. Recursos extras serão habilitados apenas quando não prejudicarem a experiência na televisão.
