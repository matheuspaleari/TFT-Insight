from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def check(name: str, ok: bool, detail: str = "") -> bool:
    status = "OK" if ok else "BLOQUEAR"
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {name}{suffix}")
    return ok


def text(path: str) -> str:
    p = ROOT / path
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""


def main() -> int:
    print("=" * 100)
    print("AUDITORIA 73 - DEPLOY + PERSISTENCIA")
    print("=" * 100)

    results = []

    run_api = text("run_api.py")
    results.append(check(
        "API não presa em 127.0.0.1",
        'host="127.0.0.1"' not in run_api
        and "host='127.0.0.1'" not in run_api,
    ))
    results.append(check(
        "API suporta porta de ambiente",
        'os.getenv("PORT"' in run_api,
    ))

    context = text("partner_platform/platform_core/context.py")
    auth_client = text("partner_platform/auth/api_client.py")
    results.append(check(
        "Frontend usa configuração de API para produção",
        "TFT_INSIGHT_API_BASE_URL" in context
        or "TFT_INSIGHT_API_BASE_URL" in auth_client,
    ))

    auth_db = text("src/integration_engine/auth/database.py")
    results.append(check(
        "Autenticação não depende exclusivamente de SQLite local",
        "DATABASE_URL" in text("src/persistence/database_url.py")
        and "sqlite3" not in auth_db,
    ))

    analytics_repo = text("src/partner_analytics/repository.py")
    results.append(check(
        "Analytics não depende exclusivamente de SQLite local",
        "DATABASE_URL" in text("src/persistence/database_url.py")
        and "sqlite3" not in analytics_repo,
    ))

    gitignore = text(".gitignore")
    results.append(check(".env ignorado pelo Git", re.search(r"(?m)^\.env$", gitignore) is not None))
    results.append(check("database/*.db ignorado", "database/*.db" in gitignore))
    results.append(check("data/partner/*.db ignorado", "data/partner/*.db" in gitignore))
    results.append(check("data/knowledge/*.db ignorado", "data/knowledge/*.db" in gitignore))
    results.append(check("data/history ignorado", "data/history/" in gitignore))
    results.append(check("data/players ignorado", "data/players/" in gitignore))

    env_example = text(".env.example")
    results.append(check(
        ".env.example declara segredo da autenticação",
        "TFT_INSIGHT_AUTH_SECRET=" in env_example,
    ))
    results.append(check(
        ".env.example pronto para DATABASE_URL",
        "DATABASE_URL=" in env_example,
    ))
    results.append(check(
        "Ollama/local AI desligado por padrão",
        "tft_insight_local_ai_enabled=false" in env_example.lower(),
    ))

    print("-" * 100)
    approved = sum(results)
    total = len(results)
    print(f"Checks aprovados: {approved}/{total}")

    if approved != total:
        print(f"RESULTADO: DEPLOY BLOQUEADO ({total-approved} pendência(s))")
        return 1

    print("RESULTADO: CÓDIGO PRONTO PARA TESTE DE DEPLOY")
    print("IMPORTANTE: ainda valide DATABASE_URL e persistência no provedor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
