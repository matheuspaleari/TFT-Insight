ROADMAP 26.1A-C — AUTENTICAÇÃO LOCAL DO TFT INSIGHT
===================================================

OBJETIVO
--------
Adicionar criação de conta, login por e-mail/senha, sessão autenticada,
logout e registro básico de acessos sem alterar a arquitetura principal
FastAPI + Streamlit.

ARQUIVOS PARA SUBSTITUIR
------------------------
partner_platform/app.py
src/integration_engine/api/app.py
requirements.txt
.env.example

ARQUIVOS NOVOS
--------------
partner_platform/auth/__init__.py
partner_platform/auth/api_client.py
partner_platform/auth/login_page.py
partner_platform/auth/session.py

src/integration_engine/auth/__init__.py
src/integration_engine/auth/database.py
src/integration_engine/auth/models.py
src/integration_engine/auth/password_service.py
src/integration_engine/auth/service.py
src/integration_engine/auth/token_service.py
src/integration_engine/auth/user_repository.py

src/integration_engine/api/routes/auth.py
scripts/validate_72_auth_foundation.py

O QUE A ETAPA ENTREGA
---------------------
- Cadastro normal por nome, e-mail e senha.
- E-mail único.
- Senha em hash Argon2; senha pura não é gravada.
- Login e JWT.
- /auth/me para validar sessão.
- Logout no Streamlit.
- Banco SQLite separado em database/tft_insight_auth.db.
- users, auth_identities e login_events.
- Primeiro admin definido por TFT_INSIGHT_ADMIN_EMAIL.
- Estrutura pronta para Google OAuth na etapa 26.1D.
- Login antigo de demo removido do app.py.

IMPORTANTE
----------
1. NÃO coloque segredo real no .env.example.
2. No seu .env REAL, adicione TFT_INSIGHT_AUTH_SECRET com valor aleatório.
3. O banco de autenticação não deve ir para o Git.
4. Não apague o seu .env atual; apenas acrescente as variáveis novas.
5. GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET ainda não são usados nesta etapa.

GERAR SEGREDO LOCAL
-------------------
No PowerShell, depois de ativar o venv:
python -c "import secrets; print(secrets.token_urlsafe(48))"

VALIDAÇÃO
---------
python scripts\validate_72_auth_foundation.py
