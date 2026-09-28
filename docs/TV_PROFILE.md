# Perfil técnico do aparelho

Este documento registra o alvo principal dos projetos deste repositório.

## TV

- **Fabricante:** LG
- **Família/modelo:** UK6530PSF
- **Plataforma:** webOS TV
- **Geração aproximada:** 2018
- **Firmware observado:** 05.50.70
- **Developer Mode:** disponível e já utilizado

## Objetivo de otimização

A prioridade é reduzir travamentos, engasgos de interface e reinicializações por pressão de memória.

O perfil deverá favorecer:

1. uso mínimo de memória;
2. menos observadores, timers e processamento DOM desnecessário;
3. menor retenção de buffer quando seguro;
4. ausência de AV1 neste perfil;
5. recursos externos opcionais desligados por padrão;
6. interface e reprodução compatíveis com navegadores antigos do webOS.

## Validação

Toda alteração relevante deverá ser testada na TV real antes de ser considerada estável.
