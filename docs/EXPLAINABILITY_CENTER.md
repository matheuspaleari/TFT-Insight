# Explainability Center

## Release
`v0.5.0-alpha.3`

## Objective

A interface principal deve responder:

1. O que a Engine concluiu?
2. Qual é a recomendação?
3. Qual é a condição de vitória?
4. Qual é o principal ponto de atenção?
5. Quais evidências públicas sustentam a resposta?

Dados técnicos ficam disponíveis, mas fora do fluxo principal.

## Technical Details

O componente:

```python
technical_details(payload)
```

coloca JSON bruto dentro de um `st.expander`.

Isso implementa o princípio:

```text
User experience first
Technical payload on demand
```

## Explainability page

A nova página mostra:

- Overall Score
- Top 4
- Confidence
- Expected Placement
- Pre-game Attention
- Win Condition
- Decision Path
- Prediction Evidence
- Raw API response recolhido

## Contract limitation

O Center não inventa explicações.

Quando feature contributions não existem no contrato público,
a interface informa explicitamente que aquela granularidade não
está disponível.
