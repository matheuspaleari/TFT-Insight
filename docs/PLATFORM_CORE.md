# Platform Core

## Objetivo

A Partner Platform não deve conter lógica de negócio da TFT Insight Engine.
Ela consome a API através de `services` e monta a interface por componentes.

## Fluxo

```text
Page
  ↓
PlatformPage
  ↓
Component Library
  ↓
Service
  ↓
Public API
```

## Regras

- Nenhuma lógica de negócio nas páginas.
- Nenhum CSS dentro das páginas.
- Nenhum HTML duplicado.
- Toda comunicação externa passa por services.
- Tokens visuais ficam em design_system.
