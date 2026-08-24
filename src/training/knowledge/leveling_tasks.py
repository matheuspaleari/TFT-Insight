"""
Exercícios pedagógicos relacionados à Skill de Leveling.
"""

from src.training.models import TrainingTask


PLAN_LEVEL_BEFORE_SPENDING = TrainingTask(
    id="plan_level_before_spending",
    skill_id="leveling",
    title="Planejar o próximo nível",
    description=(
        "Treina o hábito de definir antecipadamente quando utilizar "
        "ouro para comprar experiência."
    ),
    objective=(
        "Evitar decisões impulsivas de reroll ou de compra de "
        "experiência sem considerar o estado do tabuleiro."
    ),
    habit=(
        "Antes de gastar ouro, defina qual será seu próximo momento "
        "de subida de nível."
    ),
    checklist=(
        "Qual é o nível atual?",
        "Quanto ouro falta para o próximo nível?",
        "Meu tabuleiro consegue preservar vida até esse momento?",
        "Preciso estabilizar antes de comprar experiência?",
    ),
    success_signals=(
        "O jogador consegue explicar por que decidiu subir de nível.",
        "Há menos compras de experiência feitas por impulso.",
        "O jogador preserva ouro suficiente para fortalecer o tabuleiro.",
    ),
    common_mistakes=(
        "Comprar experiência sem considerar a força atual.",
        "Fazer reroll e subir de nível na mesma rodada sem planejamento.",
        "Manter um plano fixo mesmo quando o tabuleiro está muito fraco.",
    ),
    related_metric_ids=(
        "average_level",
        "average_damage_to_players",
    ),    difficulty="FOUNDATION",

)


BALANCE_LEVEL_AND_STABILITY = TrainingTask(
    id="balance_level_and_stability",
    skill_id="leveling",
    title="Equilibrar nível e estabilidade",
    description=(
        "Treina a decisão entre investir em experiência ou fortalecer "
        "as unidades que já estão no tabuleiro."
    ),
    objective=(
        "Reconhecer quando subir de nível gera mais valor e quando "
        "é necessário estabilizar antes."
    ),
    habit=(
        "Antes de comprar experiência, pergunte se uma unidade adicional "
        "realmente deixará o tabuleiro mais forte."
    ),
    checklist=(
        "Tenho uma unidade útil para colocar após subir de nível?",
        "Minhas unidades principais estão evoluídas?",
        "Estou perdendo muita vida por rodada?",
        "Quanto ouro restará depois da subida?",
    ),
    success_signals=(
        "O jogador evita subir de nível sem possuir uma unidade útil.",
        "O tabuleiro mantém força após a compra de experiência.",
        "Há menos rodadas perdidas por falta de estabilização.",
    ),
    common_mistakes=(
        "Subir de nível apenas porque o timing padrão chegou.",
        "Ignorar a perda de vida enquanto acumula experiência.",
        "Chegar ao novo nível sem ouro para melhorar o tabuleiro.",
    ),
    related_metric_ids=(
        "average_level",
        "average_damage_to_players",
        "average_players_eliminated",
    ),    difficulty="INTERMEDIATE",

)


AVOID_UNPLANNED_REROLLS = TrainingTask(
    id="avoid_unplanned_rerolls",
    skill_id="leveling",
    title="Evitar rerolls sem planejamento",
    description=(
        "Treina o controle do gasto de ouro para que rerolls não "
        "comprometam a progressão de nível."
    ),
    objective=(
        "Reduzir rerolls realizados sem uma unidade-alvo ou sem um "
        "critério claro de estabilização."
    ),
    habit=(
        "Antes de rerollar, defina quais unidades procura e quanto ouro "
        "está disposto a gastar."
    ),
    checklist=(
        "Quais unidades estou procurando?",
        "Qual melhoria realmente estabiliza o tabuleiro?",
        "Qual é meu limite de gasto nesta rodada?",
        "Esse gasto prejudicará meu próximo nível?",
    ),
    success_signals=(
        "O jogador inicia o reroll com unidades-alvo definidas.",
        "O gasto termina ao atingir o limite planejado.",
        "A progressão de nível deixa de ser comprometida por rerolls aleatórios.",
    ),
    common_mistakes=(
        "Rerollar sem saber quais unidades procura.",
        "Continuar gastando depois de atingir o objetivo inicial.",
        "Consumir todo o ouro tentando melhorar unidades pouco relevantes.",
    ),
    related_metric_ids=(
        "average_level",
    ),    difficulty="ADVANCED",

)


LEVELING_TASKS: tuple[TrainingTask, ...] = (
    PLAN_LEVEL_BEFORE_SPENDING,
    BALANCE_LEVEL_AND_STABILITY,
    AVOID_UNPLANNED_REROLLS,
)