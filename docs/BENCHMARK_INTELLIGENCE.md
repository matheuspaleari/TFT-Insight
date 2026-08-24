# Benchmark Intelligence

## Release
`v0.5.0-alpha.2`

## Data sources

The module uses existing TFT Insight data:

```text
data/analysis/challenger_metrics.csv
data/role_inference/challenger/matches/*.json
```

The player identity catalog is persisted at:

```text
data/benchmark/challenger_player_catalog.json
```

No Riot API request is required to build the catalog. Riot IDs are
recovered from cached match payloads.

## Public endpoints

```http
GET /v1/benchmark/challenger
POST /v1/benchmark/challenger/compare/player
```

## Percentiles

Percentiles are calculated against the actual player distribution
stored in `challenger_metrics.csv`.

For metrics where lower is better, such as average placement and
placement standard deviation, the percentile direction is inverted.

## Challenger Explorer

The Partner Platform exposes an `ⓘ Players used` popover. By default
it displays only the Riot IDs, keeping the benchmark page uncluttered.

## Cache

The player catalog is persistent. Run:

```powershell
python scripts/build_challenger_player_catalog.py
```

to rebuild it manually.
