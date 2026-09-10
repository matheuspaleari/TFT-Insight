from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def check(label: str, ok: bool) -> bool:
    print(f"[{'OK' if ok else 'FALHOU'}] {label}")
    return ok


def main() -> int:
    print("=" * 100)
    print("VALIDACAO 72 - ROADMAP 26.1A-C: AUTENTICACAO LOCAL")
    print("=" * 100)

    temp_dir = Path(tempfile.mkdtemp(prefix="tft_auth_validate_"))
    db_path = temp_dir / "auth_test.db"

    old_env = {
        key: os.environ.get(key)
        for key in (
            "TFT_INSIGHT_AUTH_DB_PATH",
            "TFT_INSIGHT_AUTH_SECRET",
            "TFT_INSIGHT_ADMIN_EMAIL",
            "TFT_INSIGHT_AUTH_TOKEN_MINUTES",
        )
    }

    os.environ["TFT_INSIGHT_AUTH_DB_PATH"] = str(db_path)
    os.environ["TFT_INSIGHT_AUTH_SECRET"] = (
        "validation-only-secret-0123456789-abcdefghijklmnopqrstuvwxyz"
    )
    os.environ["TFT_INSIGHT_ADMIN_EMAIL"] = "admin@example.com"
    os.environ["TFT_INSIGHT_AUTH_TOKEN_MINUTES"] = "60"

    try:
        from src.integration_engine.auth.database import initialize_database
        from src.integration_engine.auth.service import AuthError, AuthService
        from src.integration_engine.auth.user_repository import UserRepository

        initialize_database()
        repo = UserRepository()
        service = AuthService(repository=repo)

        checks: list[bool] = []

        checks.append(check("banco SQLite criado", db_path.exists()))

        user, token = service.register(
            email=" Admin@Example.com ",
            display_name="Matheus Teste",
            password="SenhaTeste123",
        )
        checks.append(check("cadastro normal cria usuário", user.id > 0))
        checks.append(check("e-mail normalizado", user.email == "admin@example.com"))
        checks.append(check("admin inicial por e-mail", user.role == "admin"))
        checks.append(check("senha não exposta no usuário", "password" not in user.public_dict()))
        checks.append(check("token JWT emitido", isinstance(token, str) and len(token) > 20))

        stored_hash = repo.get_password_hash(user.id) or ""
        checks.append(check("senha armazenada como hash Argon2", stored_hash.startswith("$argon2")))
        checks.append(check("senha pura não aparece no hash", "SenhaTeste123" not in stored_hash))

        me = service.user_from_token(token)
        checks.append(check("token recupera usuário correto", me.id == user.id))

        logged, login_token = service.login(
            email="admin@example.com",
            password="SenhaTeste123",
        )
        checks.append(check("login válido funciona", logged.id == user.id and bool(login_token)))

        wrong_password_blocked = False
        try:
            service.login(
                email="admin@example.com",
                password="senha-errada",
            )
        except AuthError:
            wrong_password_blocked = True
        checks.append(check("senha inválida é bloqueada", wrong_password_blocked))

        duplicate_blocked = False
        try:
            service.register(
                email="ADMIN@example.com",
                display_name="Outro Nome",
                password="OutraSenha123",
            )
        except AuthError:
            duplicate_blocked = True
        checks.append(check("e-mail duplicado é bloqueado", duplicate_blocked))

        weak_password_blocked = False
        try:
            service.register(
                email="novo@example.com",
                display_name="Novo",
                password="12345678",
            )
        except AuthError:
            weak_password_blocked = True
        checks.append(check("senha fraca é bloqueada", weak_password_blocked))

        checks.append(check("eventos de login são registrados", repo.count_login_events() >= 3))

        from src.integration_engine.api.routes.auth import router
        paths = {route.path for route in router.routes}
        checks.append(check("/auth/register existe", "/auth/register" in paths))
        checks.append(check("/auth/login existe", "/auth/login" in paths))
        checks.append(check("/auth/me existe", "/auth/me" in paths))

        total = len(checks)
        passed = sum(checks)

        print("-" * 100)
        print(f"Checks aprovados: {passed}/{total}")

        if passed == total:
            print("RESULTADO: FUNDAÇÃO DE AUTENTICAÇÃO VALIDADA")
            return 0

        print("RESULTADO: VALIDAÇÃO 72 COM PENDÊNCIAS")
        return 1
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
