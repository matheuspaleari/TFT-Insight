# Setup e execução do TFT Insight

Este guia descreve o caminho suportado para preparar e executar o TFT Insight localmente.

A aplicação atual possui dois processos:

```text
Terminal 1                     Terminal 2
──────────                     ──────────
FastAPI                        Streamlit
python run_api.py              python scripts\run_partner_platform.py
      │                               │
      └──── http://127.0.0.1:8000 ────┘
```

A Partner Platform utiliza a API local para executar as análises.

---

## 1. Pré-requisitos

Para executar o projeto, tenha disponível:

- Python;
- `pip`;
- Git, caso esteja clonando o repositório;
- uma chave válida da Riot API para análises reais;
- Ollama apenas se quiser habilitar a narrativa local opcional.

O projeto não depende do Ollama para calcular métricas, prioridades ou planos de treinamento.

---

## 2. Clone o repositório

```powershell
git clone https://github.com/matheuspaleari/TFT-Insight.git
cd TFT-Insight
```

---

## 3. Ambiente virtual

Crie um ambiente virtual fora ou dentro do projeto conforme sua preferência.

Exemplo genérico no Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No ambiente de desenvolvimento original do projeto, o ambiente virtual é externo à pasta do repositório e pode ser ativado com:

```powershell
& "C:\Users\user\Desktop\tft-insight-venv\Scripts\Activate.ps1"
```

> A pasta de ambiente virtual não deve ser publicada no Git.

Confirme que o Python utilizado é o do ambiente:

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

---

## 4. Dependências

Com o ambiente virtual ativo:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

As dependências incluem as bibliotecas usadas pelo backend FastAPI, Partner Platform Streamlit, visualizações, configuração e comunicação HTTP.

---

## 5. Arquivo `.env`

Crie um arquivo chamado:

```text
.env
```

na raiz do projeto.

O `.env` é local e não deve ser enviado ao Git.

### Riot API

Para executar análises reais, configure:

```dotenv
RIOT_API_KEY=sua_chave_aqui
```

O cliente Riot exige `RIOT_API_KEY`; sem ela, a integração real com a Riot API não pode ser inicializada.

Não coloque uma chave real em:

- `README.md`;
- documentação;
- `.env.example`;
- commits;
- screenshots;
- logs compartilhados.

---

## 6. Narrativa local com Ollama — opcional

A camada de narrativa local é opcional.

Configuração suportada:

```dotenv
TFT_INSIGHT_LOCAL_AI_ENABLED=false
TFT_INSIGHT_LOCAL_AI_MODEL=llama3.2:3b
TFT_INSIGHT_OLLAMA_URL=http://localhost:11434
TFT_INSIGHT_LOCAL_AI_TIMEOUT=45
```

Com `TFT_INSIGHT_LOCAL_AI_ENABLED=false`, o projeto continua operando sem depender do narrador local.

Para usar Ollama, instale-o separadamente, disponibilize o modelo configurado e altere:

```dotenv
TFT_INSIGHT_LOCAL_AI_ENABLED=true
```

A disponibilidade do Ollama não muda a regra arquitetural do produto:

> **A Engine calcula e decide; o narrador apenas comunica contratos já calculados.**

---

## 7. Inicie a API

Abra o primeiro terminal, ative o ambiente virtual e execute:

```powershell
python run_api.py
```

A configuração local utilizada pela Partner Platform aponta por padrão para:

```text
http://127.0.0.1:8000
```

Mantenha esse terminal aberto.

---

## 8. Inicie a Partner Platform

Abra um segundo terminal.

Ative novamente o mesmo ambiente virtual:

```powershell
& "C:\Users\user\Desktop\tft-insight-venv\Scripts\Activate.ps1"
```

Depois:

```powershell
python scripts\run_partner_platform.py
```

Esse é o entrypoint suportado da interface atual:

```text
scripts/run_partner_platform.py
        ↓
partner_platform/app.py
```

A Partner Platform carrega o `.env` da raiz e inicia a aplicação Streamlit.

---

## 9. Verifique a conexão

Na barra lateral da Partner Platform existe um estado de sistema.

Com a API iniciada corretamente, a interface deve indicar que a API está online.

Se a API estiver offline:

1. confirme que o terminal do backend continua aberto;
2. confirme que `python run_api.py` iniciou sem erro;
3. confirme que a URL configurada na interface é `http://127.0.0.1:8000`;
4. confirme que os dois terminais estão usando o ambiente virtual correto.

A configuração técnica da interface permite informar:

- API Base URL;
- API Key da própria plataforma, quando aplicável;
- ambiente de execução.

Esses campos são diferentes da `RIOT_API_KEY` usada pelo backend para falar com a Riot Games.

---

## 10. Primeira análise

Com backend e interface ativos:

1. abra a Partner Platform;
2. informe Riot ID e tag;
3. escolha o benchmark disponível na interface;
4. execute a análise.

O fluxo real usa a API e o pipeline interno para transformar o histórico em performance, contexto, evidências e coaching.

---

## 11. Validação rápida

Antes de investigar problemas de interface, confirme a integridade básica do projeto:

```powershell
python scripts\validate_51_roadmap24_official_suite.py --profile quick
```

Esse perfil valida:

- arquivos críticos;
- sintaxe Python;
- imports principais;
- grafos de importação da plataforma e sessão.

---

## 12. Validação completa

Antes de release, commit estrutural ou depois de uma limpeza:

```powershell
python scripts\validate_51_roadmap24_official_suite.py --profile full
```

Para incluir os guardrails:

```powershell
python scripts\validate_51_roadmap24_official_suite.py --profile full --guardrails
```

---

## 13. Smoke test manual

Depois de a suíte automatizada passar, valide o caminho público:

```text
[ ] API inicia sem traceback
[ ] Partner Platform abre
[ ] Sidebar mostra API online
[ ] Home renderiza
[ ] Navegação funciona
[ ] Riot ID vazio é tratado como estado de produto
[ ] Analisar dispara a requisição
[ ] Resultado é renderizado
[ ] Composição abre/renderiza
[ ] Contestação abre/renderiza
[ ] Economia abre/renderiza
[ ] Carries + Itens abre/renderiza
[ ] Erros não exibem dumps técnicos ao usuário
```

Esse smoke test complementa a suíte automática porque valida interação e renderização reais.

---

## 14. Troubleshooting

### `RIOT_API_KEY` não encontrada

Sintoma típico:

```text
A variável RIOT_API_KEY não foi encontrada no arquivo .env.
```

Confira:

```text
TFT-Insight/
├── .env
├── run_api.py
├── requirements.txt
└── ...
```

E confirme que o `.env` contém:

```dotenv
RIOT_API_KEY=...
```

Reinicie a API depois de alterar variáveis de ambiente.

### API offline na Partner Platform

Primeiro teste:

```powershell
python run_api.py
```

Se o backend iniciar, mantenha-o aberto e reinicie a interface em outro terminal:

```powershell
python scripts\run_partner_platform.py
```

### `ModuleNotFoundError`

Ative o ambiente virtual e reinstale as dependências:

```powershell
& "C:\Users\user\Desktop\tft-insight-venv\Scripts\Activate.ps1"

pip install -r requirements.txt
```

### PowerShell bloqueia `Activate.ps1`

Isso depende da política de execução configurada no Windows. Não altere políticas de segurança global apenas para executar o projeto sem entender o impacto.

Você também pode chamar diretamente o Python do ambiente virtual ou ajustar a política apenas de acordo com as regras do seu próprio ambiente.

### Caracteres estranhos no terminal

Alguns terminais Windows podem usar encodings diferentes de UTF-8.

Os testes oficiais evitam depender de símbolos Unicode para indicar sucesso. Se um script histórico apresentar erro apenas ao imprimir um símbolo, diferencie falha de console de falha funcional antes de alterar código de domínio.

### Ollama indisponível

Se você não precisa da narrativa local, mantenha:

```dotenv
TFT_INSIGHT_LOCAL_AI_ENABLED=false
```

A lógica determinística deve continuar funcionando.

---

## 15. O que não publicar

Antes de qualquer commit/push, revise especialmente:

```text
.env
.venv/
tft-insight-venv/
__pycache__/
*.pyc
logs locais
arquivos temporários
credenciais
```

A existência de `.gitignore` ajuda, mas não substitui a revisão do `git status`.

---

## 16. Comandos de referência

### Terminal 1 — API

```powershell
& "C:\Users\user\Desktop\tft-insight-venv\Scripts\Activate.ps1"

python run_api.py
```

### Terminal 2 — Partner Platform

```powershell
& "C:\Users\user\Desktop\tft-insight-venv\Scripts\Activate.ps1"

python scripts\run_partner_platform.py
```

### Validação rápida

```powershell
& "C:\Users\user\Desktop\tft-insight-venv\Scripts\Activate.ps1"

python scripts\validate_51_roadmap24_official_suite.py --profile quick
```

### Validação completa

```powershell
& "C:\Users\user\Desktop\tft-insight-venv\Scripts\Activate.ps1"

python scripts\validate_51_roadmap24_official_suite.py --profile full --guardrails
```

---

## 17. Sequência recomendada

Para uma instalação nova:

```text
Clone
  ↓
Ambiente virtual
  ↓
requirements.txt
  ↓
.env + RIOT_API_KEY
  ↓
API
  ↓
Partner Platform
  ↓
Quick validation
  ↓
Primeira análise
```

Para desenvolvimento diário:

```text
Ativar venv
  ↓
Subir API
  ↓
Subir Partner Platform
  ↓
Desenvolver
  ↓
Quick
  ↓
Full + guardrails antes de mudanças estruturais/release
```
