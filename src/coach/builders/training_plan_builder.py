"""
Constrói um plano de treinamento a partir do contexto do Coach.
"""

from src.coach.models import (
    CoachContext,
    CoachMetric,
    TrainingPlan,
)


class TrainingPlanBuilder:
    """
    Converte a principal prioridade do jogador
    em um plano estruturado de evolução.
    """

    @classmethod
    def build(
        cls,
        context: CoachContext,
    ) -> TrainingPlan:
        """
        Cria um plano de treinamento baseado na métrica
        de maior impacto disponível no contexto.
        """

        priority = context.main_metric

        if priority is None:
            raise ValueError(
                "Não é possível criar um plano de treinamento "
                "sem uma métrica prioritária."
            )

        return TrainingPlan(
            focus_metric_id=priority.id,
            focus_title=priority.title,
            diagnosis=cls._build_diagnosis(priority),
            objective=cls._build_objective(priority),
            games_target=5,
            actions=cls._build_actions(priority),
            checklist=cls._build_checklist(priority),
            common_mistakes=cls._build_common_mistakes(priority),
            expected_improvements=cls._build_expected_improvements(
                priority
            ),
            monitored_metrics=cls._build_monitored_metrics(
                context=context,
                priority=priority,
            ),
            learning_title=cls._build_learning_title(priority),
            learning_content=cls._build_learning_content(priority),
        )

    @staticmethod
    def _build_diagnosis(
        priority: CoachMetric,
    ) -> str:
        if priority.category == "result":
            return (
                f"Sua principal oportunidade de evolução está em "
                f"{priority.title.lower()}. Essa é uma métrica de "
                "resultado, portanto não deve ser melhorada de forma "
                "direta. Ela pode indicar que alguns fatores ligados "
                "à força do tabuleiro ainda não estão sendo convertidos "
                "em pressão suficiente sobre os adversários."
            )

        if priority.category == "consistency":
            return (
                f"Sua principal oportunidade de evolução está em "
                f"{priority.title.lower()}. Essa métrica representa "
                "a estabilidade do seu desempenho entre partidas e "
                "pode indicar oscilações nas decisões ou na execução."
            )

        return (
            f"Sua principal oportunidade de evolução está em "
            f"{priority.title.lower()}. Essa métrica está mais "
            "diretamente relacionada às decisões tomadas durante "
            "a partida."
        )

    @staticmethod
    def _build_objective(
        priority: CoachMetric,
    ) -> str:
        if priority.category == "result":
            return (
                f"Nas próximas partidas, trabalhe os fatores que "
                f"influenciam {priority.title.lower()}, em vez de "
                "tentar aumentar essa métrica diretamente."
            )

        return (
            f"Nas próximas partidas, concentre-se em melhorar "
            f"{priority.title.lower()} de forma consciente e repetível."
        )

    @staticmethod
    def _build_actions(
        priority: CoachMetric,
    ) -> tuple[str, ...]:
        if priority.recommendations:
            return priority.recommendations[:5]

        return (
            "Acompanhe essa métrica durante as próximas partidas.",
        )

    @staticmethod
    def _build_checklist(
        priority: CoachMetric,
    ) -> tuple[str, ...]:
        metric_id = priority.id

        if metric_id == "average_level":
            return (
                "Defini antes da rodada se preciso subir de nível?",
                "Meu tabuleiro está forte o suficiente para economizar?",
                "Estou fazendo reroll sem considerar o custo de experiência?",
                "Subir de nível agora melhora realmente meu tabuleiro?",
            )

        if metric_id == "average_damage_to_players":
            return (
                "Tenho componentes ou itens completos sem utilizar?",
                "Meu tabuleiro está forte para este estágio da partida?",
                "Adaptei meu posicionamento aos possíveis adversários?",
                "Estou convertendo uma sequência de vitórias em pressão?",
            )

        if metric_id == "average_players_eliminated":
            return (
                "Meu tabuleiro está estabilizado para este estágio?",
                "Estou economizando mesmo enquanto perco muita vida?",
                "Tenho componentes ou itens parados?",
                "Observei quais adversários estão mais vulneráveis?",
                "Meu posicionamento favorece os próximos confrontos?",
            )

        if metric_id == "placement_standard_deviation":
            return (
                "Estou seguindo um plano coerente para minha composição?",
                "Adaptei minhas decisões aos itens e unidades disponíveis?",
                "Estou assumindo riscos desnecessários?",
                "Minha tomada de decisão muda demais entre partidas?",
            )

        return tuple(
            f"Estou acompanhando o fator: {driver}?"
            for driver in priority.drivers[:5]
        ) or (
            "Estou acompanhando conscientemente essa prioridade?",
        )

    @staticmethod
    def _build_common_mistakes(
        priority: CoachMetric,
    ) -> tuple[str, ...]:
        metric_id = priority.id

        if metric_id == "average_level":
            return (
                "Subir de nível sem ter ouro suficiente para estabilizar.",
                "Fazer rerolls cedo demais e comprometer a progressão.",
                "Economizar enquanto o tabuleiro perde muita vida.",
            )

        if metric_id == "average_damage_to_players":
            return (
                "Manter componentes sem uso por várias rodadas.",
                "Ignorar o posicionamento dos principais adversários.",
                "Chegar aos estágios intermediários com um tabuleiro fraco.",
            )

        if metric_id == "average_players_eliminated":
            return (
                "Esperar a composição perfeita antes de investir ouro.",
                "Estabilizar somente depois de perder muita vida.",
                "Não adaptar itens e posicionamento aos adversários.",
                "Manter vantagem econômica sem convertê-la em força.",
            )

        if metric_id == "placement_standard_deviation":
            return (
                "Forçar sempre a mesma composição.",
                "Alterar o plano sem considerar os recursos disponíveis.",
                "Assumir riscos elevados sem necessidade.",
            )

        return (
            "Tentar melhorar o resultado sem trabalhar seus fatores causais.",
        )

    @staticmethod
    def _build_expected_improvements(
        priority: CoachMetric,
    ) -> tuple[str, ...]:
        metric_id = priority.id

        if metric_id == "average_level":
            return (
                "Maior nível médio nas partidas.",
                "Mais acesso a unidades de custo elevado.",
                "Maior flexibilidade para fortalecer o tabuleiro.",
            )

        if metric_id == "average_damage_to_players":
            return (
                "Aumento do dano médio causado aos adversários.",
                "Maior preservação de sequências de vitória.",
                "Maior pressão nos estágios intermediários.",
            )

        if metric_id == "average_players_eliminated":
            return (
                "Aumento da média de eliminações.",
                "Aumento do dano causado aos adversários.",
                "Maior capacidade de converter vantagem em resultado.",
            )

        if metric_id == "placement_standard_deviation":
            return (
                "Menor oscilação entre partidas.",
                "Resultados mais previsíveis.",
                "Maior consistência na colocação média.",
            )

        return (
            f"Evolução gradual em {priority.title.lower()}.",
        )

    @staticmethod
    def _build_monitored_metrics(
        *,
        context: CoachContext,
        priority: CoachMetric,
    ) -> tuple[str, ...]:
        related_metrics = [
            priority.id,
        ]

        for metric in context.metrics:
            if metric.id not in related_metrics:
                related_metrics.append(metric.id)

            if len(related_metrics) == 3:
                break

        return tuple(related_metrics)

    @staticmethod
    def _build_learning_title(
        priority: CoachMetric,
    ) -> str:
        if priority.id == "average_players_eliminated":
            return "Como converter vantagem em pressão"

        if priority.id == "average_damage_to_players":
            return "Como construir pressão durante a partida"

        if priority.id == "average_level":
            return "Quando transformar ouro em níveis"

        if priority.id == "placement_standard_deviation":
            return "Como reduzir oscilações entre partidas"

        return priority.title

    @staticmethod
    def _build_learning_content(
        priority: CoachMetric,
    ) -> str:
        drivers = ", ".join(priority.drivers)

        if priority.category == "result":
            return (
                f"{priority.title} é uma consequência de outras decisões. "
                f"Os fatores relacionados cadastrados são: {drivers}. "
                "O objetivo do treino é melhorar esses fatores para que "
                "o resultado evolua naturalmente."
            )

        return (
            f"{priority.description} Os fatores mais relacionados são: "
            f"{drivers}."
        )