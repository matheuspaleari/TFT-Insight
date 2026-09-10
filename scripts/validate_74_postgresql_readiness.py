from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def check(label: str, ok: bool) -> bool:
    print(f"[{'OK' if ok else 'FALHOU'}] {label}")
    return ok


def main() -> int:
    print("=" * 100)
    print("VALIDACAO 74 - ROADMAP 27.1 POSTGRESQL / DEPLOY")
    print("=" * 100)

    results = []

    run_api = read("run_api.py")
    auth_db = read("src/integration_engine/auth/database.py")
    analytics = read("src/partner_analytics/repository.py")
    context = read("partner_platform/platform_core/context.py")
    env = read(".env.example")
    req = read("requirements.txt")

    results.append(check(
        "API aceita HOST de ambiente",
        'os.getenv("HOST", "0.0.0.0")' in run_api,
    ))
    results.append(check(
        "API aceita PORT de ambiente",
        'os.getenv("PORT", "8000")' in run_api,
    ))
    results.append(check(
        "Auth usa DATABASE_URL",
        "get_database_url" in auth_db and "sqlite3" not in auth_db,
    ))
    results.append(check(
        "Analytics usa DATABASE_URL",
        "get_database_url" in analytics and "sqlite3" not in analytics,
    ))
    results.append(check(
        "Frontend usa TFT_INSIGHT_API_BASE_URL",
        "TFT_INSIGHT_API_BASE_URL" in context,
    ))
    results.append(check(
        "ConfiguraÃ§Ã£o tÃ©cnica escondida em Production",
        'configured_environment.lower() == "production"' in context,
    ))
    results.append(check(
        ".env.example possui DATABASE_URL",
        re.search(r"(?m)^DATABASE_URL=", env) is not None,
    ))
    results.append(check(
        ".env.example possui HOST/PORT",
        "HOST=" in env and "PORT=" in env,
    ))
    results.append(check(
        "psycopg incluÃ­do nas dependÃªncias",
        re.search(r"(?m)^psycopg\[binary\]$", req) is not None,
    ))
    results.append(check(
        "script de migraÃ§Ã£o existe",
        (ROOT / "scripts" / "migrate_sqlite_to_postgres_27_1.py").exists(),
    ))

    configured = bool(os.getenv("DATABASE_URL", "").strip())
    if configured:
        try:
            from src.integration_engine.auth.database import initialize_database
            from src.partner_analytics import PartnerAnalyticsRepository
            initialize_database()
            PartnerAnalyticsRepository().initialize()
            results.append(check("ConexÃ£o PostgreSQL real", True))
        except Exception as exc:
            print(f"[FALHOU] ConexÃ£o PostgreSQL real â€” {exc}")
            results.append(False)
    else:
        print("[INFO] DATABASE_URL nÃ£o configurada: teste de conexÃ£o real foi pulado.")

    print("-" * 100)
    passed = sum(results)
    total = len(results)
    print(f"Checks aprovados: {passed}/{total}")

    if passed == total:
        if configured:
            print("RESULTADO: POSTGRESQL E CONFIGURAÃ‡ÃƒO DE DEPLOY VALIDADOS")
        else:
            print("RESULTADO: CÃ“DIGO PRONTO; FALTA CONFIGURAR DATABASE_URL E TESTAR CONEXÃƒO")
        return 0

    print("RESULTADO: ROADMAP 27.1 COM PENDÃŠNCIAS")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

