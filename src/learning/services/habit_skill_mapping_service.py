from __future__ import annotations

from collections import defaultdict

from src.learning.models.habit import Habit
from src.learning.models.skill_level import SkillLevel
from src.learning.models.skill_signal import SkillSignal


class HabitSkillMappingService:
    """
    Converte Habits em sinais de Skill.

    Regras:
    - não acessa Riot API;
    - não usa IA;
    - não altera o significado dos Habits;
    - não transforma evidência contextual em domínio de Skill;
    - não substitui SkillMappingService nem SkillAssessment;
    - Habits podem reforçar uma Skill oficial sem necessariamente
      sugerir um nível de domínio.

    A integração definitiva com o catálogo de Skills pode consumir estes
    sinais sem duplicar a lógica de detecção de hábitos.
    """

    @classmethod
    def map(
        cls,
        *,
        habits: tuple[Habit, ...],
    ) -> tuple[SkillSignal, ...]:
        raw_signals = [
            signal
            for habit in habits
            for signal in cls._map_habit(
                habit
            )
        ]

        grouped: dict[
            str,
            list[SkillSignal],
        ] = defaultdict(list)

        for signal in raw_signals:
            grouped[
                signal.skill_id
            ].append(signal)

        merged = tuple(
            cls._merge_skill_signals(
                skill_id,
                signals,
            )
            for skill_id, signals
            in grouped.items()
        )

        return tuple(
            sorted(
                merged,
                key=cls._signal_order,
            )
        )

    @classmethod
    def _map_habit(
        cls,
        habit: Habit,
    ) -> tuple[SkillSignal, ...]:
        evidence_ids = tuple(
            evidence.key
            for evidence in habit.evidence
        )

        if habit.habit_id == "consistent_level_progression":
            return (
                SkillSignal(
                    skill_id="leveling",
                    skill_label="Progressão de nível",
                    direction="positive",
                    confidence=habit.confidence,
                    assessable=False,
                    level_hint=None,
                    habit_ids=(
                        habit.habit_id,
                    ),
                    evidence_ids=evidence_ids,
                    interpretation=(
                        "O histórico reforça positivamente a Skill de "
                        "progressão de nível ao mostrar que o jogador chega "
                        "a níveis altos de forma recorrente. Esse padrão não "
                        "define, sozinho, o nível global da Skill de Leveling."
                    ),
                    limitations=(
                        (
                            "Chegar recorrentemente aos níveis 8 ou 9 não "
                            "mede o ritmo da progressão em relação ao benchmark."
                        ),
                        (
                            "O histórico não reconstrói o timing exato de "
                            "compra de experiência."
                        ),
                    ),
                ),
            )

        if habit.habit_id == "late_low_level_pattern":
            return (
                SkillSignal(
                    skill_id="leveling",
                    skill_label="Progressão de nível",
                    direction="negative",
                    confidence=habit.confidence,
                    assessable=False,
                    level_hint=None,
                    habit_ids=(
                        habit.habit_id,
                    ),
                    evidence_ids=evidence_ids,
                    interpretation=(
                        "O histórico adiciona evidência negativa relacionada "
                        "à progressão tardia, mas não determina sozinho o "
                        "nível global da Skill de Leveling."
                    ),
                    limitations=(
                        (
                            "A evidência mostra o resultado final da "
                            "progressão, não as decisões econômicas "
                            "intermediárias nem o ritmo frente ao benchmark."
                        ),
                    ),
                ),
            )

        if habit.habit_id == "resources_remaining_at_end":
            return (
                SkillSignal(
                    skill_id="economy",
                    skill_label="Economia",
                    direction="context",
                    confidence=habit.confidence,
                    assessable=False,
                    level_hint=None,
                    habit_ids=(
                        habit.habit_id,
                    ),
                    evidence_ids=evidence_ids,
                    interpretation=(
                        "Há um padrão relacionado à conversão de recursos, "
                        "mas os dados atuais não observam timing de gasto, "
                        "juros ou rerolls o suficiente para atribuir nível "
                        "de domínio à Skill de economia."
                    ),
                    limitations=(
                        (
                            "Ouro final isolado não informa quando o "
                            "recurso deveria ou poderia ter sido gasto."
                        ),
                    ),
                ),
            )

        if habit.habit_id == "composition_flexibility":
            return (
                SkillSignal(
                    skill_id="composition_flexibility",
                    skill_label="Flexibilidade de composição",
                    direction="positive",
                    confidence=habit.confidence,
                    assessable=True,
                    level_hint=SkillLevel.ADVANCED,
                    habit_ids=(
                        habit.habit_id,
                    ),
                    evidence_ids=evidence_ids,
                    interpretation=(
                        "A alta variedade recorrente sustenta evidência "
                        "positiva de flexibilidade entre composições."
                    ),
                    limitations=(
                        (
                            "A análise observa variedade entre partidas, "
                            "não todas as opções disponíveis dentro de "
                            "cada lobby."
                        ),
                    ),
                ),
            )

        if habit.habit_id == "composition_variety":
            return (
                SkillSignal(
                    skill_id="composition_flexibility",
                    skill_label="Flexibilidade de composição",
                    direction="positive",
                    confidence=habit.confidence,
                    assessable=True,
                    level_hint=SkillLevel.COMPETENT,
                    habit_ids=(
                        habit.habit_id,
                    ),
                    evidence_ids=evidence_ids,
                    interpretation=(
                        "A variedade observada sustenta um sinal positivo "
                        "de flexibilidade, ainda abaixo do nível de evidência "
                        "usado para considerar o padrão estabelecido."
                    ),
                    limitations=(
                        (
                            "A Skill é inferida a partir da variedade "
                            "histórica entre partidas."
                        ),
                    ),
                ),
            )

        if habit.habit_id == "composition_concentration":
            level = (
                SkillLevel.BEGINNER
                if habit.status == "established"
                else SkillLevel.DEVELOPING
            )

            return (
                SkillSignal(
                    skill_id="composition_flexibility",
                    skill_label="Flexibilidade de composição",
                    direction="negative",
                    confidence=habit.confidence,
                    assessable=True,
                    level_hint=level,
                    habit_ids=(
                        habit.habit_id,
                    ),
                    evidence_ids=evidence_ids,
                    interpretation=(
                        "A concentração recorrente sustenta um sinal "
                        "negativo para flexibilidade entre composições."
                    ),
                    limitations=(
                        (
                            "Concentração histórica não prova que o "
                            "jogador deliberadamente forçou uma linha."
                        ),
                    ),
                ),
            )

        if habit.habit_id == "recurring_carry_contest_exposure":
            return (
                SkillSignal(
                    skill_id="lobby_reading",
                    skill_label="Leitura de lobby",
                    direction="context",
                    confidence=habit.confidence,
                    assessable=False,
                    level_hint=None,
                    habit_ids=(
                        habit.habit_id,
                    ),
                    evidence_ids=evidence_ids,
                    interpretation=(
                        "A exposição recorrente à contestação é contexto "
                        "relevante para leitura de lobby, mas não mostra "
                        "se o jogador identificou a contestação, quando "
                        "identificou ou como reagiu a ela."
                    ),
                    limitations=(
                        (
                            "Sem observação de scouting ou decisões durante "
                            "a partida, não é seguro atribuir nível à Skill "
                            "de leitura de lobby."
                        ),
                    ),
                ),
            )

        return ()

    @classmethod
    def _merge_skill_signals(
        cls,
        skill_id: str,
        signals: list[SkillSignal],
    ) -> SkillSignal:
        if len(signals) == 1:
            return signals[0]

        assessable = [
            signal
            for signal in signals
            if signal.assessable
            and signal.level_hint is not None
        ]

        if not assessable:
            strongest = max(
                signals,
                key=lambda item: item.confidence,
            )

            directions = {
                signal.direction
                for signal in signals
            }

            if len(directions) == 1:
                direction = strongest.direction
            else:
                direction = "context"

            return SkillSignal(
                skill_id=skill_id,
                skill_label=strongest.skill_label,
                direction=direction,
                confidence=max(
                    signal.confidence
                    for signal in signals
                ),
                assessable=False,
                level_hint=None,
                habit_ids=tuple(
                    dict.fromkeys(
                        habit_id
                        for signal in signals
                        for habit_id in signal.habit_ids
                    )
                ),
                evidence_ids=tuple(
                    dict.fromkeys(
                        evidence_id
                        for signal in signals
                        for evidence_id in signal.evidence_ids
                    )
                ),
                interpretation=(
                    "Existem múltiplas evidências históricas relacionadas "
                    "à Skill. Elas são preservadas como suporte/contexto e "
                    "não são convertidas artificialmente em nível de domínio."
                ),
                limitations=tuple(
                    dict.fromkeys(
                        limitation
                        for signal in signals
                        for limitation in signal.limitations
                    )
                ),
            )

        strongest = max(
            assessable,
            key=lambda item: item.confidence,
        )

        return SkillSignal(
            skill_id=skill_id,
            skill_label=strongest.skill_label,
            direction=strongest.direction,
            confidence=strongest.confidence,
            assessable=True,
            level_hint=strongest.level_hint,
            habit_ids=tuple(
                dict.fromkeys(
                    habit_id
                    for signal in signals
                    for habit_id in signal.habit_ids
                )
            ),
            evidence_ids=tuple(
                dict.fromkeys(
                    evidence_id
                    for signal in signals
                    for evidence_id in signal.evidence_ids
                )
            ),
            interpretation=(
                "O nível sugerido usa a evidência avaliável de maior "
                "confiança. Evidências apenas contextuais permanecem "
                "como suporte e não alteram o nível sugerido."
            ),
            limitations=tuple(
                dict.fromkeys(
                    limitation
                    for signal in signals
                    for limitation in signal.limitations
                )
            ),
        )

    @staticmethod
    def _signal_order(
        signal: SkillSignal,
    ) -> tuple[bool, int, float]:
        level_value = (
            int(signal.level_hint)
            if signal.level_hint is not None
            else 999
        )

        return (
            not signal.assessable,
            level_value,
            -signal.confidence,
        )
