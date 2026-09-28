# Build v0.1.0 — perfil UK6530

Upstream fixado: `NicholasBly/youtube-webos@5f7aa18fa0829b4e0607475222d5adacd85c6eff`

## Alterações desta primeira build

- bloqueio de anúncios permanece ligado e não pode ser desativado acidentalmente;
- bloqueio de telemetria passa a vir ligado no perfil inicial;
- codec padrão: **Avoid AV1**;
- SponsorBlock desligado no perfil inicial;
- Return YouTube Dislike removido do runtime desta variante;
- melhoria de miniaturas desligada no perfil inicial;
- qualidade máxima forçada desligada;
- relógio da interface desligado;
- correção legada de emojis desligada no perfil inicial;
- retenção do buffer traseiro reduzida de 30 s para 20 s;
- ID do aplicativo preservado como `youtube.leanback.v4` para funcionar como atualização da instalação AdFree existente;
- versão do pacote elevada para `0.8.4`;
- título visível alterado para **YouTube UK6530**.

## Critério

Esta é uma build de teste, não uma declaração de desempenho final. O objetivo do primeiro teste na TV real é verificar:

1. abertura da tela inicial;
2. fluidez das setas e menus;
3. início de vídeos;
4. ausência de propagandas;
5. estabilidade em vídeos longos;
6. estabilidade após várias trocas de vídeo;
7. comportamento após 30–60 minutos.

Só depois desses testes vamos avançar para otimizações mais agressivas.
