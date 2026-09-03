from __future__ import annotations

from typing import Any

import streamlit as st

from partner_platform.components.insight_banner import insight_banner

# ---------------------------------------------------------------------------
# Garantia visual do modal de métricas em produção
# ---------------------------------------------------------------------------
# Em alguns ambientes, o st.dialog pode herdar a superfície clara do tema
# nativo do Streamlit mesmo quando o restante do TFT Insight está em dark.
# Esta regra afeta somente os dialogs e não altera a lógica pedagógica.
st.markdown(
    """
    <style>
    [data-testid="stDialog"] [role="dialog"],
    [data-testid="stDialog"] > div > div[role="dialog"],
    div[role="dialog"] {
        background: #0f131a !important;
        background-color: #0f131a !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 18px 50px rgba(0, 0, 0, 0.45) !important;
    }

    [data-testid="stDialog"] [role="dialog"] > div,
    [data-testid="stDialog"] [role="dialog"] section {
        background: #0f131a !important;
        background-color: #0f131a !important;
    }

    [data-testid="stDialog"] [role="dialog"] h1,
    [data-testid="stDialog"] [role="dialog"] h2,
    [data-testid="stDialog"] [role="dialog"] h3,
    [data-testid="stDialog"] [role="dialog"] h4,
    [data-testid="stDialog"] [role="dialog"] p,
    [data-testid="stDialog"] [role="dialog"] label,
    [data-testid="stDialog"] [role="dialog"] [data-testid="stMetricLabel"],
    [data-testid="stDialog"] [role="dialog"] [data-testid="stMetricValue"] {
        color: #f8fafc !important;
    }

    [data-testid="stDialog"] [role="dialog"] [data-testid="stCaptionContainer"],
    [data-testid="stDialog"] [role="dialog"] [data-testid="stCaptionContainer"] p {
        color: #94a3b8 !important;
    }

    [data-testid="stDialog"] [role="dialog"] button,
    [data-testid="stDialog"] [role="dialog"] button svg {
        color: #f8fafc !important;
        fill: currentColor !important;
    }

    [data-testid="stDialog"] [role="dialog"] [data-testid="stAlert"] {
        background: #17324b !important;
        background-color: #17324b !important;
        border-color: rgba(96, 165, 250, 0.20) !important;
    }

    [data-testid="stDialog"] [role="dialog"] [data-testid="stAlert"] p {
        color: #60a5fa !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)



_METRIC_ALIASES = {
    "Taxa de vitória": "win_rate",
    "Taxa de Top 4": "top4_rate",
    "Colocação média": "average_placement",
    "Dano aos jogadores": "average_damage_to_players",
    "Eliminações por partida": "average_players_eliminated",
    "Nível médio": "average_level",
    "Consistência": "placement_standard_deviation",
}

_REVERSE_ALIASES = {
    "Win rate": "win_rate",
    "Top 4": "top4_rate",
    "Average placement": "average_placement",
    "Damage": "average_damage_to_players",
    "Average level": "average_level",
    "Consistency": "placement_standard_deviation",
    "win_rate": "win_rate",
    "top4_rate": "top4_rate",
    "average_placement": "average_placement",
    "average_damage_to_players": "average_damage_to_players",
    "average_players_eliminated": "average_players_eliminated",
    "average_level": "average_level",
    "placement_standard_deviation": "placement_standard_deviation",
}

_METRIC_DETAILS = {
    "win_rate": {
        "title": "Taxa de vitória",
        "meaning": "Mostra em quantas partidas você terminou em 1º lugar dentro da amostra analisada.",
        "measurement": "O TFT Insight divide o número de vitórias pelo total de partidas analisadas e compara sua taxa com a do grupo competitivo.",
        "why_it_matters": "Vitória mede sua capacidade de converter partidas fortes em 1º lugar. Ela complementa o Top 4: é possível chegar com frequência entre os quatro primeiros e ainda ter dificuldade para transformar essas boas partidas em vitórias.",
        "decimals": 1,
        "percent": True,
        "lower_is_better": False,
    },
    "top4_rate": {
        "title": "Taxa de Top 4",
        "meaning": "Mostra em quantas partidas você terminou entre as quatro primeiras colocações.",
        "measurement": "O TFT Insight divide a quantidade de Top 4 pelo total de partidas analisadas e compara sua taxa com a do grupo competitivo.",
        "why_it_matters": "Top 4 representa frequência de resultados positivos. Uma taxa alta indica que você consegue evitar eliminações precoces e chegar com regularidade à metade superior do lobby.",
        "decimals": 1,
        "percent": True,
        "lower_is_better": False,
    },
    "average_placement": {
        "title": "Colocação média",
        "meaning": "Resume sua posição final média nas partidas analisadas. Em TFT, valores menores são melhores: 1,0 representa uma média de primeiro lugar.",
        "measurement": "O TFT Insight calcula a média das colocações finais e compara o resultado com o grupo competitivo.",
        "why_it_matters": "A colocação média combina partidas boas e ruins em uma leitura geral de resultado. Ela ajuda a mostrar se seu histórico recente está terminando, em média, mais perto do topo ou do fundo do lobby.",
        "decimals": 2,
        "percent": False,
        "lower_is_better": True,
    },
    "average_damage_to_players": {
        "title": "Dano aos jogadores",
        "meaning": "Mede o dano médio causado aos outros jogadores nas partidas analisadas. É um sinal de quanto a força do seu tabuleiro está sendo convertida em pressão no lobby.",
        "measurement": "O TFT Insight calcula a média do dano total causado aos jogadores e compara esse valor com o grupo competitivo.",
        "why_it_matters": "Dano mais alto costuma acompanhar tabuleiros que vencem rodadas e pressionam o lobby. Ele não explica sozinho a qualidade das decisões e deve ser lido junto das demais evidências.",
        "decimals": 1,
        "percent": False,
        "lower_is_better": False,
    },
    "average_players_eliminated": {
        "title": "Eliminações por partida",
        "meaning": "Mede quantos adversários você elimina, em média, nas partidas analisadas.",
        "measurement": "O TFT Insight calcula a média de jogadores eliminados por partida e compara esse resultado com o grupo competitivo.",
        "why_it_matters": "A métrica ajuda a mostrar sua capacidade de transformar vantagem em eliminações concretas no lobby.",
        "decimals": 2,
        "percent": False,
        "lower_is_better": False,
    },
    "average_level": {
        "title": "Nível médio",
        "meaning": "Mede o nível final médio alcançado nas partidas analisadas.",
        "measurement": "O TFT Insight calcula o nível final médio e compara esse valor com o grupo competitivo.",
        "why_it_matters": "O nível alcançado está ligado à gestão de ouro, timing de subida de nível, rerolls e necessidade de estabilizar o tabuleiro. O valor não diz sozinho se subir de nível foi correto em cada partida.",
        "decimals": 2,
        "percent": False,
        "lower_is_better": False,
    },
    "placement_standard_deviation": {
        "title": "Consistência",
        "meaning": "Aqui, consistência significa estabilidade das suas colocações entre partidas. Ela não mede diretamente se você está colocando bem; mede o quanto seus resultados oscilam.",
        "measurement": "O TFT Insight usa o desvio-padrão das colocações. Quanto menor esse valor, menor a variação entre suas posições finais e, portanto, maior a consistência.",
        "why_it_matters": "Dois jogadores podem ter colocação média parecida, mas um alternar entre 1º e 8º enquanto outro termina quase sempre perto da mesma faixa. A consistência diferencia esses dois padrões.",
        "decimals": 2,
        "percent": False,
        "lower_is_better": True,
    },
}


def _normalize(value: Any) -> str:
    return str(value or "").strip()


def _public_metric_key(item: dict[str, Any] | None) -> str:
    if not isinstance(item, dict):
        return ""
    raw = _normalize(item.get("metric") or item.get("label"))
    return _REVERSE_ALIASES.get(raw, raw)


def _find_comparison(*, metric_title: str, comparisons: list[dict[str, Any]]) -> dict[str, Any] | None:
    expected_key = _METRIC_ALIASES.get(metric_title)
    for item in comparisons:
        if not isinstance(item, dict):
            continue
        if expected_key and _public_metric_key(item) == expected_key:
            return item
        if _normalize(item.get("label")) == metric_title:
            return item
    return None


def _as_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _number(value: Any, *, decimals: int = 2, percent: bool = False) -> str:
    number = _as_float(value)
    if number is None:
        return "N/A"
    # O contrato atual usa taxas em pontos percentuais. Não recalculamos valores.
    suffix = "%" if percent else ""
    return f"{number:.{decimals}f}".replace(".", ",") + suffix


def _benchmark_value(item: dict[str, Any] | None, key: str) -> Any:
    if not isinstance(item, dict):
        return None
    direct_keys = {
        "mean": ("benchmark_mean", "challenger_mean"),
        "median": ("benchmark_median", "challenger_median"),
    }
    for candidate in direct_keys.get(key, ()):
        value = item.get(candidate)
        if value is not None:
            return value
    benchmark_metric = item.get("benchmark_metric")
    if isinstance(benchmark_metric, dict):
        return benchmark_metric.get(key)
    return None


def _gap_percent(player: float | None, benchmark: float | None) -> float | None:
    if player is None or benchmark in (None, 0):
        return None
    return (player - benchmark) / abs(benchmark) * 100.0


def _comparison_sentence(
    *,
    metric_key: str,
    details: dict[str, Any],
    player: float | None,
    benchmark: float | None,
    benchmark_name: str,
) -> str:
    if player is None or benchmark is None:
        return "Não há valores comparáveis suficientes para justificar esta leitura numericamente."

    diff = player - benchmark
    gap = _gap_percent(player, benchmark)
    lower_is_better = bool(details.get("lower_is_better"))

    if abs(diff) < 1e-9:
        return f"Seu resultado está praticamente igual à média de {benchmark_name}."

    better = diff < 0 if lower_is_better else diff > 0
    direction = "melhor" if better else "pior"
    relation = "abaixo" if diff < 0 else "acima"

    if metric_key == "placement_standard_deviation":
        consequence = (
            "Isso significa que suas colocações oscilaram menos entre partidas, "
            "o que representa maior estabilidade de resultado."
            if better else
            "Isso significa que suas colocações oscilaram mais entre partidas, "
            "o que representa menor estabilidade de resultado."
        )
    elif metric_key == "average_placement":
        consequence = (
            "Como colocação média é uma métrica em que números menores são melhores, "
            "isso indica finais de partida, em média, mais próximos do topo."
            if better else
            "Como colocação média é uma métrica em que números menores são melhores, "
            "isso indica finais de partida, em média, mais distantes do topo."
        )
    elif metric_key == "win_rate":
        consequence = (
            "Na prática, você está convertendo uma parcela maior das partidas em 1º lugar."
            if better else
            "Na prática, você está convertendo uma parcela menor das partidas em 1º lugar."
        )
    elif metric_key == "top4_rate":
        consequence = (
            "Na prática, você chega à metade superior do lobby com mais frequência."
            if better else
            "Na prática, você chega à metade superior do lobby com menos frequência."
        )
    elif metric_key == "average_level":
        consequence = (
            "Seu histórico termina, em média, em níveis mais altos; isso pode refletir mais acesso a níveis tardios, sem provar sozinho que o timing de level foi correto."
            if better else
            "Seu histórico termina, em média, em níveis mais baixos; isso pode estar ligado a gasto para estabilizar, reroll ou menor acesso aos níveis tardios, mas a métrica sozinha não identifica a causa."
        )
    elif metric_key == "average_damage_to_players":
        consequence = (
            "Isso indica maior conversão da força do tabuleiro em pressão sobre os adversários."
            if better else
            "Isso indica menor conversão da força do tabuleiro em pressão sobre os adversários."
        )
    elif metric_key == "average_players_eliminated":
        consequence = (
            "Isso mostra que sua força de tabuleiro chega a eliminar adversários com mais frequência."
            if better else
            "Isso mostra que sua força de tabuleiro chega a eliminar adversários com menos frequência."
        )
    else:
        consequence = "A diferença posiciona seu histórico recente em relação ao padrão competitivo."

    gap_text = f" ({abs(gap):.1f}% de diferença relativa)" if gap is not None else ""
    return (
        f"Seu valor ficou {relation} da média de {benchmark_name}{gap_text}. "
        f"Nesta métrica, isso é um resultado {direction} em relação à referência. {consequence}"
    )


def _cross_metric_context(
    *,
    metric_key: str,
    comparisons: list[dict[str, Any]],
) -> str | None:
    by_key = {
        _public_metric_key(item): item
        for item in comparisons
        if isinstance(item, dict)
    }

    def relation(key: str) -> int | None:
        item = by_key.get(key)
        if not item:
            return None
        p = _as_float(item.get("player_value"))
        b = _as_float(_benchmark_value(item, "mean"))
        if p is None or b is None:
            return None
        if abs(p - b) < 1e-9:
            return 0
        lower = bool(_METRIC_DETAILS.get(key, {}).get("lower_is_better"))
        better = p < b if lower else p > b
        return 1 if better else -1

    win = relation("win_rate")
    top4 = relation("top4_rate")

    if metric_key == "win_rate":
        if win == -1 and top4 in (0, 1):
            return (
                "Leitura conjunta: sua frequência de Top 4 está próxima ou acima da referência, "
                "mas sua taxa de vitória está abaixo. Isso sugere que você consegue construir "
                "partidas competitivas, porém está convertendo poucas delas em 1º lugar."
            )
        if win == -1 and top4 == -1:
            return (
                "Leitura conjunta: vitória e Top 4 estão abaixo da referência. O sinal não aponta "
                "apenas para dificuldade de fechar partidas em 1º; a perda de resultado começa antes, "
                "na frequência com que você consegue chegar à metade superior do lobby."
            )
        if win == 1 and top4 == -1:
            return (
                "Leitura conjunta: você vence relativamente bem quando a partida encaixa, mas chega "
                "ao Top 4 com menos frequência. Seu perfil recente parece mais volátil: bons jogos "
                "convertem, porém há espaço para aumentar a frequência de partidas estáveis."
            )

    if metric_key == "top4_rate":
        if top4 == -1 and win == 1:
            return (
                "Leitura conjunta: quando suas partidas chegam ao ponto de disputar o topo, você "
                "converte bem em vitórias; o principal contraste está em chegar ao Top 4 com mais frequência."
            )
        if top4 == 1 and win == -1:
            return (
                "Leitura conjunta: você chega ao Top 4 com boa frequência, mas transforma poucas "
                "dessas partidas em vitória. O próximo salto de resultado está mais ligado à conversão "
                "de boas partidas em 1º lugar do que simplesmente a sobreviver até o Top 4."
            )

    return None


def _pedagogical_reading(
    *,
    metric_key: str,
    details: dict[str, Any],
    comparison: dict[str, Any] | None,
    comparisons: list[dict[str, Any]],
    benchmark_name: str,
) -> tuple[str, str | None]:
    if not isinstance(comparison, dict):
        return (
            "O TFT Insight não encontrou os valores comparativos necessários para justificar esta classificação com números.",
            None,
        )

    player = _as_float(comparison.get("player_value"))
    benchmark = _as_float(_benchmark_value(comparison, "mean"))

    justification = _comparison_sentence(
        metric_key=metric_key,
        details=details,
        player=player,
        benchmark=benchmark,
        benchmark_name=benchmark_name,
    )
    context = _cross_metric_context(metric_key=metric_key, comparisons=comparisons)
    return justification, context


@st.dialog("Detalhes da métrica", width="large")
def _metric_details_dialog(
    *,
    metric_title: str,
    summary: str,
    comparison: dict[str, Any] | None,
    comparisons: list[dict[str, Any]],
    benchmark_name: str,
) -> None:
    metric_key = (
        _METRIC_ALIASES.get(metric_title)
        or (_public_metric_key(comparison) if isinstance(comparison, dict) else "")
    )

    details = _METRIC_DETAILS.get(metric_key)
    if details is None:
        st.markdown(f"## {metric_title}")
        st.caption(summary)
        st.warning(
            "Esta métrica ainda não possui uma explicação pedagógica cadastrada. "
            "O TFT Insight não vai substituir isso por um texto genérico."
        )
        return

    st.markdown(f"## {details['title']}")
    st.caption(summary)

    st.markdown("### O que esta métrica avalia")
    st.write(details["meaning"])

    st.markdown("### Como sua nota é formada")
    st.write(details["measurement"])

    if isinstance(comparison, dict):
        decimals = int(details.get("decimals", 2))
        percent = bool(details.get("percent", False))
        player_value = comparison.get("player_value")
        benchmark_mean = _benchmark_value(comparison, "mean")
        benchmark_median = _benchmark_value(comparison, "median")

        cols = st.columns(3)
        with cols[0]:
            st.metric("Seu resultado", _number(player_value, decimals=decimals, percent=percent))
        with cols[1]:
            st.metric(
                f"Média · {benchmark_name}",
                _number(benchmark_mean, decimals=decimals, percent=percent),
            )
        with cols[2]:
            st.metric(
                "Mediana da referência",
                _number(benchmark_median, decimals=decimals, percent=percent),
            )

        percentile = comparison.get("percentile")
        if percentile is not None:
            st.caption("Percentil comparativo: " + _number(percentile, decimals=0))

    justification, cross_context = _pedagogical_reading(
        metric_key=metric_key,
        details=details,
        comparison=comparison,
        comparisons=comparisons,
        benchmark_name=benchmark_name,
    )

    st.markdown("### Por que você recebeu esta avaliação")
    st.write(justification)

    if cross_context:
        st.info(cross_context, icon="🎓")

    st.markdown("### Por que isso importa no jogo")
    st.write(details["why_it_matters"])

    if metric_key == "placement_standard_deviation":
        st.info(
            "Importante: consistência não significa automaticamente jogar bem. "
            "Um jogador pode ser consistente terminando sempre em 5º, por exemplo. "
            "Aqui estamos avaliando a estabilidade das colocações; a qualidade dessas "
            "colocações aparece em métricas como colocação média, Top 4 e vitória.",
            icon="ℹ️",
        )

    st.caption(
        "A explicação acima usa os mesmos valores comparativos já calculados pelo TFT Insight; "
        "o componente não cria uma nova nota nem altera a classificação."
    )


def render_metric_detail_card(
    *,
    eyebrow: str,
    metric_title: str,
    summary: str,
    comparisons: list[dict[str, Any]],
    benchmark_name: str,
    tone: str,
    key: str,
) -> None:
    """
    Renderiza o resumo visual e explica pedagogicamente a classificação.

    Nenhuma métrica é recalculada aqui. O componente usa os valores já
    devolvidos pela comparação para justificar a leitura apresentada.
    """
    insight_banner(
        eyebrow=eyebrow,
        title=metric_title,
        description=summary,
        tone=tone,
    )

    comparison = _find_comparison(
        metric_title=metric_title,
        comparisons=comparisons,
    )

    if st.button(
        "Entender minha avaliação →",
        key=key,
        use_container_width=True,
    ):
        _metric_details_dialog(
            metric_title=metric_title,
            summary=summary,
            comparison=comparison,
            comparisons=comparisons,
            benchmark_name=benchmark_name,
        )
