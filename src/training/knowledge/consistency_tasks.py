"""
Exercícios pedagógicos relacionados à consistência entre partidas.
"""

from src.training.models import TrainingTask


DEFINE_A_SIMPLE_GAME_PLAN = TrainingTask(
    id="define_simple_game_plan",
    skill_id="consistency",
    title="Definir um plano simples",
    description=(
        "Treina a criação de um plano básico antes de executar decisões "
        "importantes durante a partida."
    ),
    objective=(
        "Reduzir mudanças impulsivas e aumentar a repetibilidade das "
        "decisões entre partidas."
    ),
    habit=(
        "Em cada estágio, defina um objetivo principal e mantenha-o "
        "até surgir uma razão concreta para mudar."
    ),
    checklist=(
        "Qual é meu objetivo neste estágio?",
        "Estou economizando, estabilizando ou subindo de nível?",
        "O que precisa acontecer para eu mudar o plano?",
        "Minha decisão atual está alinhada ao objetivo?",
    ),
    success_signals=(
        "As decisões seguem um objetivo compreensível.",
        "Há menos mudanças de direção por impulso.",
        "O jogador consegue explicar por que alterou o plano.",
    ),
    common_mistakes=(
        "Mudar o plano após uma única derrota.",
        "Tentar executar vários objetivos simultaneamente.",
        "Forçar o plano mesmo quando os recursos não o sustentam.",
    ),
    related_metric_ids=(
        "placement_standard_deviation",
        "average_level",
    ),    difficulty="FOUNDATION",

)


REVIEW_ONE_DECISION_PER_MATCH = TrainingTask(
    id="review_one_decision_per_match",
    skill_id="consistency",
    title="Revisar uma decisão por partida",
    description=(
        "Treina a reflexão objetiva sobre uma decisão importante "
        "tomada durante cada partida."
    ),
    objective=(
        "Identificar padrões de erro sem sobrecarregar o jogador "
        "com uma revisão completa da partida."
    ),
    habit=(
        "Ao terminar a partida, registre uma decisão que repetiria "
        "e uma que faria de forma diferente."
    ),
    checklist=(
        "Qual decisão teve maior impacto?",
        "Que informação eu possuía naquele momento?",
        "A decisão foi coerente com meu plano?",
        "O que farei diferente na próxima partida?",
    ),
    success_signals=(
        "O jogador identifica decisões específicas, não apenas resultados.",
        "Erros repetidos começam a ser reconhecidos.",
        "A próxima partida possui um ajuste claro.",
    ),
    common_mistakes=(
        "Avaliar somente a colocação final.",
        "Culpar apenas itens ou unidades disponíveis.",
        "Tentar revisar todos os acontecimentos da partida.",
    ),
    related_metric_ids=(
        "placement_standard_deviation",
    ),    difficulty="INTERMEDIATE",

)


REDUCE_UNNECESSARY_RISK = TrainingTask(
    id="reduce_unnecessary_risk",
    skill_id="consistency",
    title="Reduzir riscos desnecessários",
    description=(
        "Treina a identificação de decisões que aumentam a variância "
        "sem oferecer retorno proporcional."
    ),
    objective=(
        "Diminuir partidas muito ruins causadas por apostas excessivas "
        "ou decisões sem plano de recuperação."
    ),
    habit=(
        "Antes de uma decisão arriscada, identifique a alternativa "
        "mais segura e compare os possíveis resultados."
    ),
    checklist=(
        "Qual é o benefício esperado dessa decisão?",
        "O que acontece se ela falhar?",
        "Existe uma opção mais estável?",
        "Minha vida e economia permitem assumir esse risco?",
    ),
    success_signals=(
        "Há menos decisões de tudo ou nada sem necessidade.",
        "O jogador preserva opções de recuperação.",
        "As colocações apresentam menor oscilação.",
    ),
    common_mistakes=(
        "Confundir risco elevado com jogada de alto nível.",
        "Investir todo o ouro sem plano alternativo.",
        "Forçar uma composição apesar da falta de recursos.",
    ),
    related_metric_ids=(
        "placement_standard_deviation",
    ),    difficulty="ADVANCED",

)


CONSISTENCY_TASKS: tuple[TrainingTask, ...] = (
    DEFINE_A_SIMPLE_GAME_PLAN,
    REVIEW_ONE_DECISION_PER_MATCH,
    REDUCE_UNNECESSARY_RISK,
)