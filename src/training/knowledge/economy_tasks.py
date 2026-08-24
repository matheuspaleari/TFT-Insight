"""
Exercícios pedagógicos relacionados à Skill de Economia.

O Performance Engine ainda não avalia essa Skill diretamente.
Esses exercícios ficam disponíveis para quando houver evidências
suficientes ou quando forem selecionados como pré-requisito.
"""

from src.training.models import TrainingTask


DEFINE_SPENDING_LIMIT = TrainingTask(
    id="define_spending_limit",
    skill_id="economy",
    title="Definir limite de gasto",
    description=(
        "Treina o jogador a decidir antecipadamente quanto ouro pode "
        "investir sem destruir completamente sua economia."
    ),
    objective=(
        "Evitar gastos impulsivos e manter clareza sobre o objetivo "
        "de cada investimento."
    ),
    habit=(
        "Antes de gastar, defina quanto ouro será utilizado e qual "
        "resultado deve ser alcançado."
    ),
    checklist=(
        "Quanto ouro possuo?",
        "Quanto posso gastar sem comprometer o próximo plano?",
        "Qual melhoria estou buscando?",
        "Em qual valor de ouro devo parar?",
    ),
    success_signals=(
        "O jogador termina o gasto próximo do limite definido.",
        "Cada investimento possui um objetivo claro.",
        "Há menos rodadas em que todo o ouro é consumido sem estabilização.",
    ),
    common_mistakes=(
        "Gastar sem definir um limite.",
        "Continuar rerollando depois de encontrar a melhoria necessária.",
        "Preservar economia enquanto perde vida em excesso.",
    ),
    related_metric_ids=(
        "average_level",
        "average_damage_to_players",
    ),
)


CONVERT_GOLD_INTO_STRENGTH = TrainingTask(
    id="convert_gold_into_strength",
    skill_id="economy",
    title="Converter economia em força",
    description=(
        "Treina o reconhecimento do momento em que o ouro acumulado "
        "precisa ser transformado em nível, unidades ou estabilidade."
    ),
    objective=(
        "Evitar manter uma economia saudável enquanto o tabuleiro "
        "continua perdendo vida."
    ),
    habit=(
        "Ao perder rodadas consecutivas, avalie se o ouro guardado "
        "deve ser convertido em força imediatamente."
    ),
    checklist=(
        "Quanto de vida estou perdendo por combate?",
        "Meu tabuleiro está abaixo da força esperada para o estágio?",
        "Qual investimento gera força imediata?",
        "Guardar esse ouro vale a vida que provavelmente perderei?",
    ),
    success_signals=(
        "O jogador investe antes de entrar em uma situação crítica.",
        "A perda de vida diminui após o investimento.",
        "O ouro é convertido em melhorias observáveis no tabuleiro.",
    ),
    common_mistakes=(
        "Priorizar juros mesmo quando o tabuleiro está muito fraco.",
        "Gastar ouro sem identificar a melhoria necessária.",
        "Esperar perder muita vida antes de estabilizar.",
    ),
    related_metric_ids=(
        "average_damage_to_players",
        "average_players_eliminated",
        "average_level",
    ),
)


PLAN_TWO_ROUNDS_AHEAD = TrainingTask(
    id="plan_two_rounds_ahead",
    skill_id="economy",
    title="Planejar duas rodadas à frente",
    description=(
        "Treina a criação de um plano econômico simples para as "
        "próximas rodadas."
    ),
    objective=(
        "Reduzir decisões isoladas e conectar economia, nível e "
        "estabilidade em um plano de curto prazo."
    ),
    habit=(
        "Ao início de cada estágio, defina o que pretende fazer nas "
        "duas próximas rodadas."
    ),
    checklist=(
        "Vou economizar, subir de nível ou rerollar?",
        "Quanto ouro espero possuir na próxima rodada?",
        "Meu tabuleiro suporta esse plano?",
        "Qual situação me fará abandonar o plano?",
    ),
    success_signals=(
        "O jogador possui um plano antes da rodada começar.",
        "As decisões econômicas seguem uma sequência coerente.",
        "O plano é adaptado quando vida, unidades ou adversários mudam.",
    ),
    common_mistakes=(
        "Decidir apenas depois que a rodada começa.",
        "Seguir o plano mesmo quando o tabuleiro está colapsando.",
        "Tentar economizar, subir de nível e rerollar simultaneamente.",
    ),
    related_metric_ids=(
        "average_level",
        "average_damage_to_players",
    ),
)


ECONOMY_TASKS: tuple[TrainingTask, ...] = (
    DEFINE_SPENDING_LIMIT,
    CONVERT_GOLD_INTO_STRENGTH,
    PLAN_TWO_ROUNDS_AHEAD,
)