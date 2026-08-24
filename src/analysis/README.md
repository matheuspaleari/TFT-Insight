# Pasta `analysis`

Ferramentas offline para estudar quais métricas ajudam a explicar a colocação média.

## Dependências

```bash
pip install pandas scikit-learn
```

## Construir o dataset

```python
from src.analysis.dataset_builder import DatasetBuilder

dataset = DatasetBuilder().build([
    ("Jogador 1", player_1_metrics),
    ("Jogador 2", player_2_metrics),
])

dataset.to_csv("data/analysis/challenger_metrics.csv", index=False)
```

## Executar as etapas 2 e 3

```bash
python -m src.analysis.analysis_runner data/analysis/challenger_metrics.csv --output data/analysis/analysis_report.txt
```

Por padrão, `top4_rate`, `bottom4_rate`, `best_placement` e `worst_placement` não entram no modelo, pois derivam diretamente da colocação e causariam vazamento de alvo. Elas continuam na correlação.

`average_gold_left` permanece como curiosidade e variável de estudo.
