from __future__ import annotations

from src.next_match_plan.models.next_match_plan import NextMatchPlan


class NextMatchPlanService:
    MAX_WATCH_ITEMS = 2

    @classmethod
    def build(
        cls,
        *,
        recommendation,
        guardrails,
        active_skill_label: str,
        mission_title: str,
        mission_objective: str = "",
    ) -> NextMatchPlan:
        if not bool(getattr(guardrails, "passed", False)):
            return NextMatchPlan(
                active_skill_label=active_skill_label,
                mission_title=mission_title,
                mission_objective=mission_objective,
                primary_title="Recomendação em revisão",
                primary_action="",
                watch_items=(),
                preserve=None,
                coach_reminder=(
                    "O Coach encontrou uma recomendação que precisa ser revisada "
                    "antes de chegar ao plano da próxima partida."
                ),
                publishable=False,
                blocked_reason=cls._blocked_reason(guardrails),
            )

        watch_items = tuple(
            str(item).strip()
            for item in (getattr(recommendation, "secondary_actions", ()) or ())
            if str(item).strip()
        )[: cls.MAX_WATCH_ITEMS]

        preserve = str(
            getattr(recommendation, "preserve", "") or ""
        ).strip() or None

        return NextMatchPlan(
            active_skill_label=active_skill_label,
            mission_title=mission_title,
            mission_objective=mission_objective,
            primary_title=str(
                getattr(recommendation, "title", "") or mission_title
            ).strip(),
            primary_action=str(
                getattr(recommendation, "recommendation", "") or mission_objective
            ).strip(),
            watch_items=watch_items,
            preserve=preserve,
            coach_reminder=(
                "Não tente corrigir tudo nesta partida. "
                "Treine uma decisão de cada vez."
            ),
            publishable=True,
            blocked_reason=None,
        )

    @staticmethod
    def _blocked_reason(guardrails) -> str:
        findings = getattr(guardrails, "findings", ()) or ()
        rule_ids = [
            str(getattr(item, "rule_id", "") or "").strip()
            for item in findings
            if str(getattr(item, "rule_id", "") or "").strip()
        ]
        if rule_ids:
            return "Guardrails bloquearam: " + ", ".join(rule_ids)
        return "Guardrails não aprovaram a recomendação."
