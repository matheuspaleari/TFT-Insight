from pathlib import Path
import re

from partner_platform.utils.display_names import (
    friendly_game_name,
    friendly_item_name,
    friendly_public_text,
)


GAME_CASES = {
    "TFT18_Zyra": "Zyra",
    "TFT18_FloraFatalis": "Flora Fatalis",
    "DA 18 Zyra": "Zyra",
    "DA18_Zyra": "Zyra",
    "DA_18_Zyra": "Zyra",
    "DA Flora Fatalis18": "Flora Fatalis",
    "DA_18_Morgana": "Morgana",
}

ITEM_CASES = {
    "TFT_Item_Deathblade": "Deathblade",
    "Item_Radiant_DeathbladeRadiant": "Deathblade Radiant",
    "Item_Artifact_InnervatingLocket": "Innervating Locket",
}

PUBLIC_TEXT_CASES = {
    "Na partida mais recente, o carry identificado foi DA_18_Morgana, com 3 itens no board final.":
        "Na partida mais recente, o carry identificado foi Morgana, com 3 itens no board final.",
    "Linha centrada em TFT18_Zyra.":
        "Linha centrada em Zyra.",
}


def main() -> None:
    for raw, expected in GAME_CASES.items():
        actual = friendly_game_name(raw)
        assert actual == expected, (raw, actual, expected)

    for raw, expected in ITEM_CASES.items():
        actual = friendly_item_name(raw)
        assert actual == expected, (raw, actual, expected)

    for raw, expected in PUBLIC_TEXT_CASES.items():
        actual = friendly_public_text(raw)
        assert actual == expected, (raw, actual, expected)

    mojibake_patterns = (
        re.compile(r"Ã[\u0080-\u00BF]"),
        re.compile(r"Â[\u0080-\u00BF]"),
        re.compile(r"â(?:€|†|‡|—|–|™|œ|ž|Ÿ|€¢|„|“|”|˜|‰|€¦|ˆ|‹|›)"),
    )
    checked_files = [
        Path("partner_platform/components/composition_intelligence.py"),
        Path("partner_platform/components/carry_item_intelligence.py"),
        Path("partner_platform/components/contest_intelligence.py"),
        Path("partner_platform/components/pre_match_coach.py"),
        Path("partner_platform/intelligence/strategic_coach_messages.py"),
    ]

    leaks = []
    for path in checked_files:
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in mojibake_patterns):
                leaks.append(f"{path}:{number}: {line.strip()}")

    assert not leaks, "Mojibake encontrado:\n" + "\n".join(leaks)

    print("OK - nomes Riot e textos públicos normalizados.")
    print("OK - nenhum mojibake encontrado nos componentes corrigidos.")


if __name__ == "__main__":
    main()
