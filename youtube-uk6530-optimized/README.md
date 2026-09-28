# YouTube UK6530 Optimized

Projeto dedicado à LG UK6530PSF.

## Meta

Entregar um cliente YouTube para webOS que preserve a experiência normal do YouTube, com bloqueio de anúncios, mas priorize fluidez e estabilidade nesta geração de TV.

## Base

Upstream analisado:

- `NicholasBly/youtube-webos`
- versão de referência inicial: 0.8.3
- licença upstream: GPL-3.0-only

## Perfil inicial proposto

- Ad Blocking: **ON**
- Reduce Telemetry & Tracking: **ON**
- Return YouTube Dislike: **OFF**
- SponsorBlock: **OFF**
- Max Thumbnail Quality: **OFF**
- Display Time: **OFF**
- Force Max Quality: **OFF**
- Force Video Codec: **Avoid AV1**
- Emoji/Characters Fix: **OFF** inicialmente
- buffer traseiro reduzido para testes controlados

## Estratégia

A implementação será feita de forma incremental:

1. estabelecer uma base funcional;
2. aplicar perfil conservador para webOS 4;
3. reduzir custo de memória e CPU;
4. gerar pacote IPK;
5. testar na TV real;
6. comparar travamentos, velocidade da interface e reprodução;
7. reativar recursos opcionais somente quando forem seguros.

Nenhuma otimização será marcada como concluída sem teste real no aparelho.
