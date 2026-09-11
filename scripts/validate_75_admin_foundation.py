from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8", errors="ignore")


def exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def check(label: str, ok: bool) -> bool:
    print(f"[{'OK' if ok else 'FALHOU'}] {label}")
    return ok


def syntax_ok(rel: str) -> bool:
    try:
        ast.parse(read(rel))
        return True
    except SyntaxError:
        return False


def main() -> int:
    print("=" * 96)
    print("VALIDACAO 75 - ROADMAP 28.1: ADMIN FOUNDATION")
    print("=" * 96)

    results: list[bool] = []

    required_files = (
        "src/integration_engine/auth/user_repository.py",
        "src/integration_engine/auth/service.py",
        "src/integration_engine/api/routes/auth.py",
        "partner_platform/auth/api_client.py",
        "partner_platform/pages/admin_page.py",
        "partner_platform/navigation/catalog.py",
        "partner_platform/platform_core/context.py",
        "partner_platform/platform_core/router.py",
    )

    for rel in required_files:
        results.append(check(
            f"arquivo existe: {rel}",
            exists(rel),
        ))

    for rel in required_files:
        results.append(check(
            f"sintaxe valida: {rel}",
            syntax_ok(rel),
        ))

    repo = read("src/integration_engine/auth/user_repository.py")
    service = read("src/integration_engine/auth/service.py")
    routes = read("src/integration_engine/api/routes/auth.py")
    client = read("partner_platform/auth/api_client.py")
    page = read("partner_platform/pages/admin_page.py")
    nav = read("partner_platform/navigation/catalog.py")
    context = read("partner_platform/platform_core/context.py")
    router = read("partner_platform/platform_core/router.py")

    results.append(check(
        "repository possui list_users",
        "def list_users(" in repo,
    ))

    results.append(check(
        "listagem ordena usuarios por criacao",
        "ORDER BY created_at DESC" in repo,
    ))

    results.append(check(
        "service possui require_admin",
        "def require_admin(" in service,
    ))

    results.append(check(
        "service valida role admin",
        'user.role != "admin"' in service,
    ))

    results.append(check(
        "service consulta usuario real a partir do token",
        "self.user_from_token(token)" in service,
    ))

    results.append(check(
        "service possui list_users_for_admin",
        "def list_users_for_admin(" in service,
    ))

    results.append(check(
        "rota /auth/admin/users existe",
        '@router.get("/admin/users")' in routes,
    ))

    results.append(check(
        "rota admin usa bearer token",
        "Depends(_bearer_token)" in routes,
    ))

    results.append(check(
        "rota admin pode retornar 403",
        "HTTP_403_FORBIDDEN" in routes,
    ))

    results.append(check(
        "frontend client possui admin_users",
        "def admin_users(" in client,
    ))

    results.append(check(
        "frontend client envia Authorization Bearer",
        'headers={"Authorization": f"Bearer {token}"}' in client,
    ))

    results.append(check(
        "pagina admin existe",
        exists("partner_platform/pages/admin_page.py"),
    ))

    results.append(check(
        "pagina admin valida role localmente",
        'user.get("role") != "admin"' in page,
    ))

    results.append(check(
        "pagina admin consulta backend protegido",
        "api_client.admin_users(token)" in page,
    ))

    results.append(check(
        "pagina admin exibe usuarios",
        "st.dataframe(" in page,
    ))

    results.append(check(
        "pagina admin exibe metricas",
        page.count(".metric(") >= 4,
    ))

    results.append(check(
        "navegacao suporta admin_only",
        "admin_only: bool = False" in nav,
    ))

    results.append(check(
        "item Admin marcado como admin_only",
        'page="Admin"' in nav
        and "admin_only=True" in nav,
    ))

    results.append(check(
        "menu filtra item admin",
        "not item.admin_only or is_admin" in nav,
    ))

    results.append(check(
        "contexto identifica role admin",
        'user.get("role") == "admin"' in context,
    ))

    results.append(check(
        "contexto passa is_admin ao catalogo",
        "is_admin=is_admin" in context,
    ))

    results.append(check(
        "router registra pagina Admin",
        '"Admin": lambda: admin_page.render(' in router,
    ))

    results.append(check(
        "router importa admin_page",
        "admin_page," in router,
    ))

    # Guardrail: não confiar somente na role do token JWT.
    token_service = read(
        "src/integration_engine/auth/token_service.py"
    )

    results.append(check(
        "JWT ainda possui role apenas como claim informativa",
        '"role": role' in token_service,
    ))

    results.append(check(
        "autorizacao admin nao decodifica role diretamente da claim",
        'payload.get("role")' not in service,
    ))

    print("-" * 96)

    passed = sum(results)
    total = len(results)

    print(f"Checks aprovados: {passed}/{total}")

    if passed == total:
        print(
            "RESULTADO: ADMIN FOUNDATION ESTRUTURALMENTE CONSISTENTE"
        )
        return 0

    print(
        f"RESULTADO: ADMIN FOUNDATION COM {total - passed} PENDENCIA(S)"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())