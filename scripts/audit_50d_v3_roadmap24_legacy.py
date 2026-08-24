from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

ADMIN_SCRIPTS = {
    "scripts/audit_50d_roadmap24_legacy.py",
    "scripts/audit_50d_v2_roadmap24_legacy.py",
    "scripts/audit_50d_v3_roadmap24_legacy.py",
    "scripts/cleanup_50e_roadmap24_archive_legacy.py",
    "scripts/validate_50f_roadmap24_smoke_after_cleanup.py",
    "scripts/validate_50f_v2_roadmap24_smoke_after_cleanup.py",
    "scripts/validate_50f_v3_roadmap24_smoke_after_cleanup.py",
}

ROADMAP_LEGACY = (
    "audit_34_roadmap21_final.py",
    "validate_35_roadmap22_shell.py",
    "validate_36a_roadmap22_intelligence.py",
    "validate_36b_roadmap22_intelligence.py",
    "validate_37_roadmap22_states.py",
    "validate_38_roadmap22_responsive.py",
    "validate_39_roadmap22_ptbr.py",
    "validate_40_roadmap22_final.py",
    "validate_40h_roadmap22_hotfix.py",
    "validate_41_roadmap23_home.py",
    "validate_42_roadmap23_navigation.py",
    "validate_43_roadmap23_how_it_works.py",
    "validate_44_roadmap23_intelligence.py",
    "validate_45_roadmap23_coach.py",
    "validate_46_roadmap23_trust.py",
    "validate_47_roadmap23_finish.py",
    "validate_48_roadmap23_final.py",
    "validate_48h_home_html_hotfix.py",
    "validate_48h2_home_render.py",
    "validate_48h3_home_navigation.py",
)

ONE_SHOT_LEGACY = (
    "finalize_25_text_fix.py",
    "finalize_25_text_fix_v2.py",
    "install_26_contestacao_avancada.py",
    "install_27_economia_avancada.py",
    "install_28_itens_carries.py",
)

POST_MATCH_SUPERSEDED = tuple(
    [f"diagnose_post_match_analysis_v1_{n}.py" for n in range(1, 7)]
    + ["diagnose_post_match_analysis_v1.py"]
    + [f"test_post_match_analysis_v1_{n}.py" for n in range(1, 7)]
    + ["test_post_match_analysis_v1.py"]
)

CANDIDATES = (
    *ROADMAP_LEGACY,
    *ONE_SHOT_LEGACY,
    *POST_MATCH_SUPERSEDED,
)


def real_references(candidate: str) -> list[str]:
    stem = Path(candidate).stem
    matches: list[str] = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in {
            ".py", ".md", ".txt", ".toml", ".yml", ".yaml"
        }:
            continue

        relative = str(path.relative_to(ROOT)).replace("\\", "/")

        if relative == f"scripts/{candidate}":
            continue
        if relative in ADMIN_SCRIPTS:
            continue
        if relative.startswith("scripts/archive/"):
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if candidate in text or stem in text:
            matches.append(relative)

    return matches


print("=" * 112)
print("#50D-V3 / ROADMAP 24.3B - AUDITORIA FINAL DE DEPENDÊNCIAS")
print("=" * 112)

present = 0
blocked = 0
archivable = 0

for candidate in CANDIDATES:
    path = SCRIPTS / candidate

    if not path.exists():
        status = "AUSENTE"
        refs = []
    else:
        present += 1
        refs = real_references(candidate)

        if refs:
            blocked += 1
            status = "DEPENDÊNCIA REAL"
        else:
            archivable += 1
            status = "ARQUIVÁVEL"

    print(f"{candidate:<66} {status}")

    for ref in refs[:8]:
        print(f"    referência real: {ref}")

print("-" * 112)
print(f"Candidatos presentes : {present}")
print(f"Arquiváveis           : {archivable}")
print(f"Dependências reais    : {blocked}")

if blocked:
    print("#50D-V3 ROADMAP 24.3B: REVISAR DEPENDÊNCIAS REAIS")
    raise SystemExit(1)

print("#50D-V3 ROADMAP 24.3B: TODOS OS CANDIDATOS LIBERADOS PARA ARQUIVO")
