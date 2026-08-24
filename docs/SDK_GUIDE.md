# Python SDK

## Instalação

```bash
pip install tft-insight
```

## Exemplo

```python
from tft_insight import TFTInsightClient

client = TFTInsightClient(api_key="...")
result = client.analyze_player("Summoner","TAG")
```

O SDK encapsula autenticação, retries e tratamento de erros.
