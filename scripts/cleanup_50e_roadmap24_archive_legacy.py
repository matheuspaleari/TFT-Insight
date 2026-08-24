from __future__ import annotations

from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

ARCHIVE_ROOT = (
    SCRIPTS
    / "archive"
    / "roadmap_legacy"
)


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


GROUPS = {
    "roadmaps": ROADMAP_LEGACY,
    "one_shot": ONE_SHOT_LEGACY,
    "post_match_superseded": POST_MATCH_SUPERSEDED,
}


moved = 0
already_archived = 0
missing = 0


for group, names in GROUPS.items():
    destination_dir = (
        ARCHIVE_ROOT
        / group
    )

    destination_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    for name in names:
        source = SCRIPTS / name
        destination = destination_dir / name

        if destination.exists():
            already_archived += 1
            continue

        if not source.exists():
            missing += 1
            continue

        shutil.move(
            str(source),
            str(destination),
        )

        moved += 1


print("=" * 110)
print("#50E / ROADMAP 24.3B - ARQUIVAMENTO CONTROLADO")
print("=" * 110)

print(
    f"Movidos para archive : {moved}"
)
print(
    f"Já arquivados        : {already_archived}"
)
print(
    f"Ausentes             : {missing}"
)

print()
print(
    "Nenhum código em src/, partner_platform/ ou data/ foi removido."
)

print(
    "Os arquivos continuam disponíveis em "
    "scripts/archive/roadmap_legacy/ para rollback."
)

print(
    "#50E ROADMAP 24.3B: ARQUIVAMENTO CONCLUÍDO"
)
