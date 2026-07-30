# TFT Insight — busca dinâmica e publicação web

## Substitua/crie estes arquivos

```text
app/streamlit_app.py
src/extract.py
src/services/player_analysis_service.py
.streamlit/secrets.toml.example
```

## Instalação local

```powershell
python -m pip install streamlit pandas requests python-dotenv
```

## Execute

```powershell
python -m streamlit run app/streamlit_app.py
```

## Configuração local no `.env`

```env
RIOT_API_KEY=RGAPI-SUA-CHAVE
MASTER_GAME_NAME=kingfelpx
MASTER_TAG_LINE=br1
MATCH_COUNT=20
```

Os campos `PLAYER_GAME_NAME` e `PLAYER_TAG_LINE` podem continuar no
`.env` para o pipeline do terminal. O dashboard utiliza o Riot ID
digitado na interface.

## Publicação

No Streamlit Community Cloud, selecione `app/streamlit_app.py` e
adicione os secrets no painel da aplicação.

A chave de desenvolvimento da Riot é temporária e não é adequada para
uma aplicação pública permanente. Para disponibilizar o produto para
outras pessoas, registre o projeto no Riot Developer Portal e solicite
uma chave adequada.

## Observação

Nesta versão, cada pesquisa baixa dados ausentes, transforma os JSONs,
atualiza o SQLite e calcula as métricas. É uma arquitetura adequada para
protótipo. Para alto volume, use banco persistente externo e fila de
processamento.
