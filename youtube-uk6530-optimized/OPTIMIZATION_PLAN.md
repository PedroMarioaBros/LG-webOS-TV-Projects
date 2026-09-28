# Plano de otimização — UK6530PSF

## Fase 1 — Base estável

- manter bloqueio de anúncios;
- manter login, histórico, inscrições, pesquisa e reprodução;
- evitar alterações visuais pesadas;
- remover dependências opcionais do caminho crítico;
- manter build legado compatível com webOS 4.

## Fase 2 — Memória

O upstream possui um limitador de `MediaSource/SourceBuffer` para webOS 3/4.

Experimento inicial:

- retenção traseira atual de referência: 30 s;
- candidato UK6530: 20 s;
- candidato agressivo: 15 s;
- intervalo de limpeza deve evitar operações excessivas de `SourceBuffer.remove()`.

A alteração deverá ser testada com vídeos longos, busca para trás e reprodução contínua.

## Fase 3 — Recursos opcionais

Desabilitar por padrão no perfil UK6530:

- Return YouTube Dislike;
- SponsorBlock;
- melhoria de miniaturas;
- relógio na interface;
- qualidade máxima forçada;
- demais recursos que façam chamadas externas ou observem continuamente o DOM.

## Fase 4 — Codec e vídeo

Padrão desejado:

- evitar AV1;
- deixar resolução adaptativa funcionar normalmente;
- não forçar a maior resolução disponível;
- comparar AVC/H.264 e VP9 na TV real quando necessário.

## Fase 5 — Medição

Observar:

- tempo até abrir a tela inicial;
- resposta às setas do controle;
- tempo para iniciar vídeo;
- travamentos durante reprodução;
- reinicializações por falta de memória;
- comportamento após 30, 60 e 120 minutos;
- troca entre vídeos consecutivos;
- retorno ao menu após vídeo longo.

## Regra

Qualquer recurso que custe estabilidade será opcional ou removido do perfil padrão da UK6530.
