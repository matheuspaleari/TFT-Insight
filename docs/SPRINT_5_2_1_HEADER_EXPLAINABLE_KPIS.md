# Sprint 5.2.1 — Smart Header + Explainable KPIs

## Smart Header

Substitui a pilha:

- Topbar
- Health Ribbon grande
- Hero

por:

- Smart Header compacto
- Compact Health Ribbon

O objetivo é reduzir a altura do topo e liberar área útil.

## Explainable KPIs

Executive agora possui explicações sob demanda para:

- Score
- Top 4
- Confidence
- Benchmark
- Expected Placement

A interação é feita pelo controle:

```text
ⓘ Por que esta nota?
```

A implementação usa `st.popover`, evitando JavaScript customizado e
mantendo compatibilidade com Streamlit puro.

## Regra de integridade

A UI não inventa pesos internos.

Quando o contrato público não fornece decomposição matemática completa,
a explicação declara explicitamente essa limitação.
