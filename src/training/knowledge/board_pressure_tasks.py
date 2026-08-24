"""
Exercícios pedagógicos relacionados à pressão de tabuleiro.
"""

from src.training.models import TrainingTask


USE_AVAILABLE_COMPONENTS = TrainingTask(
    id="use_available_components",
    skill_id="board_pressure",
    title="Transformar componentes em força",
    description=(
        "Treina o uso consciente de componentes e itens para aumentar "
        "a força imediata do tabuleiro."
    ),
    objective=(
        "Reduzir o número de rodadas jogadas com componentes parados "
        "quando eles poderiam preservar vida ou sequências de vitória."
    ),
    habit=(
        "Antes de cada combate, verifique se algum componente parado "
        "pode gerar uma melhoria relevante."
    ),
    checklist=(
        "Tenho componentes sem utilizar?",
        "Existe um item seguro que fortaleça o tabuleiro agora?",
        "Estou esperando um item perfeito enquanto perco vida?",
        "Qual unidade aproveita melhor o item disponível?",
    ),
    success_signals=(
        "Há menos componentes parados por várias rodadas.",
        "O tabuleiro recebe força antes de perder muita vida.",
        "Os itens são colocados em unidades capazes de gerar impacto.",
    ),
    common_mistakes=(
        "Esperar sempre pelo item ideal.",
        "Colocar itens sem considerar a função da unidade.",
        "Guardar componentes mesmo durante uma sequência de derrotas.",
    ),
    related_metric_ids=(
        "average_damage_to_players",
        "average_players_eliminated",
    ),
)


EVALUATE_NEXT_COMBAT = TrainingTask(
    id="evaluate_next_combat",
    skill_id="board_pressure",
    title="Avaliar a próxima luta",
    description=(
        "Treina a avaliação da força atual do tabuleiro antes de "
        "cada combate."
    ),
    objective=(
        "Criar o hábito de reconhecer quando o tabuleiro precisa "
        "de investimento imediato."
    ),
    habit=(
        "Antes do combate, responda se seu tabuleiro provavelmente "
        "vence, perde por pouco ou perde por muito."
    ),
    checklist=(
        "Minha linha de frente dura tempo suficiente?",
        "Minhas unidades principais estão causando impacto?",
        "Meu nível de força acompanha o estágio atual?",
        "Preciso gastar ouro antes da próxima luta?",
    ),
    success_signals=(
        "O jogador identifica corretamente quando está muito fraco.",
        "Os investimentos acontecem antes de grandes perdas de vida.",
        "A força do tabuleiro acompanha melhor o ritmo do lobby.",
    ),
    common_mistakes=(
        "Avaliar o tabuleiro apenas pela quantidade de estrelas.",
        "Ignorar itens, sinergias e posicionamento.",
        "Perceber a fraqueza somente depois de perder muita vida.",
    ),
    related_metric_ids=(
        "average_damage_to_players",
        "average_players_eliminated",
    ),
)


SCOUT_VULNERABLE_OPPONENTS = TrainingTask(
    id="scout_vulnerable_opponents",
    skill_id="board_pressure",
    title="Identificar adversários vulneráveis",
    description=(
        "Treina a observação dos adversários que podem ser pressionados "
        "ou eliminados nas próximas rodadas."
    ),
    objective=(
        "Converter força de tabuleiro em dano e eliminações por meio "
        "de decisões de posicionamento mais conscientes."
    ),
    habit=(
        "Antes de posicionar, observe os adversários mais prováveis "
        "e identifique quais deles estão vulneráveis."
    ),
    checklist=(
        "Quais adversários posso enfrentar?",
        "Quem possui a linha de frente mais fraca?",
        "Onde estão as principais ameaças adversárias?",
        "Meu posicionamento favorece o confronto mais provável?",
    ),
    success_signals=(
        "O jogador observa adversários antes do combate.",
        "O posicionamento muda de acordo com o lobby.",
        "A vantagem de força é convertida em mais pressão.",
    ),
    common_mistakes=(
        "Manter o mesmo posicionamento durante todo o estágio.",
        "Observar apenas o jogador em primeiro lugar.",
        "Ignorar adversários com pouca vida.",
    ),
    related_metric_ids=(
        "average_damage_to_players",
        "average_players_eliminated",
    ),
)


BOARD_PRESSURE_TASKS: tuple[TrainingTask, ...] = (
    USE_AVAILABLE_COMPONENTS,
    EVALUATE_NEXT_COMBAT,
    SCOUT_VULNERABLE_OPPONENTS,
)