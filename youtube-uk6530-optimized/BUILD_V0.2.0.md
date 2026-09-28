# Build v0.2.0 — UK6530 Lite

Esta versão é deliberadamente mais agressiva que a v0.1.0.

## Objetivo

Prioridade absoluta para:

1. ausência de anúncios servidos pelo YouTube;
2. resposta imediata do controle nos menus;
3. menor uso possível de CPU/RAM em webOS 4;
4. reprodução normal e estável.

## Removido do bundle/runtime

- painel customizado grande de configurações/atalhos (`ui.js`);
- SponsorBlock e sua interface;
- Return YouTube Dislike;
- correção Twemoji/emoji legado;
- relógio sobre a interface;
- mecanismo de miniaturas em qualidade máxima;
- forçador de qualidade máxima de vídeo;
- personalização de logo e demais recursos puxados pelo painel pesado.

A tela de **Configurações do próprio YouTube** continua existindo. O que foi removido é o painel extra do fork aberto pelo botão verde.

## Perfil fixo

- AdBlock: sempre ligado;
- telemetria extra: desligada para não manter hooks adicionais;
- Shorts: removidos;
- vídeos/entrada Ao vivo: removidos;
- Top live games: removido;
- SponsorBlock: ausente;
- miniaturas HD: ausente;
- AV1: evitado;
- previews automáticos: forçados para OFF;
- endcards: ocultos;
- buffer traseiro: 20 s.

## Navegação simplificada

São filtradas antes da renderização as categorias:

- Jogos / Gaming / Games;
- Música / Music;
- Esportes / Sports;
- Podcast / Podcasts;
- Notícias / News;
- Filmes / Movies / Movies & TV;
- Ao vivo / Live;
- Shorts (pelo filtro upstream).

A intenção é preservar o núcleo desejado: **Pesquisa, Início, Inscrições, Biblioteca e Configurações**.

## Fluidez

As transições CSS dos componentes de navegação/foco são zeradas de forma direcionada. Não usamos um bloqueio global de animações para não quebrar spinners de carregamento nem o player.

## Rollback

A v0.1.0 permanece publicada. Se a v0.2.0 apresentar regressão, é possível reinstalar a v0.1.0.
