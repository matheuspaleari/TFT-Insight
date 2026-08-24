# TFT Insight SDK — Python

SDK oficial para consumir a TFT Insight API sem montar requisições HTTP
manualmente.

## Instalação local

Na raiz do projeto:

```powershell
pip install -e .\sdk\python
```

Para instalar também as dependências de teste:

```powershell
pip install -e ".\sdk\python[dev]"
```

## Cliente síncrono

```python
from tft_insight import TFTInsightClient

with TFTInsightClient(
    base_url="http://127.0.0.1:8000",
    api_key="development",
) as client:
    report = client.analyze_player(
        game_name="Pinador doss",
        tag_line="000",
        match_count=20,
        learn=True,
    )

print(report.analysis.prediction.top4_probability)
print(report.analysis.coach.headline)
```

## Cliente assíncrono

```python
import asyncio

from tft_insight import AsyncTFTInsightClient


async def main() -> None:
    async with AsyncTFTInsightClient(
        base_url="http://127.0.0.1:8000",
        api_key="development",
    ) as client:
        report = await client.analyze_player(
            game_name="Pinador doss",
            tag_line="000",
        )

    print(report.analysis.overall_score)


asyncio.run(main())
```

## Métodos disponíveis

- `health()`
- `capabilities()`
- `analyze_signals(...)`
- `analyze_player(...)`
- `analyze_match(...)`

## Compatibilidade

O SDK espera o contrato público `1.x`. Caso a API retorne uma versão
incompatível, o SDK lança `ContractCompatibilityError`.

## Testes

```powershell
pytest .\sdk\python
```

Os testes usam transporte HTTP simulado e não acessam a Riot API.
