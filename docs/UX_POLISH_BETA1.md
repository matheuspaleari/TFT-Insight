# UX Polish — v0.5.0-beta.1

## Escopo

1. HTML centralizado e normalizado
2. Erros amigáveis
3. Busca no Challenger Explorer
4. Cards responsivos
5. Loading premium
6. Micro animações
7. Empty states

## Regra de HTML

Todo componente HTML deve usar:

```python
from partner_platform.ui import render_html
```

Nunca chamar `st.markdown()` diretamente com HTML de componente.

## Erros

A UI não deve exibir traceback ou mensagem HTTP crua no fluxo principal.

Detalhes técnicos ficam em expander.

## Loading

Playground e Explainability usam uma tela visual durante chamadas longas.

## Empty state

Páginas sem resultado mostram contexto e próxima ação, em vez de espaço vazio.
