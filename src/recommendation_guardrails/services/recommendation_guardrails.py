from __future__ import annotations
import re
from src.recommendation_guardrails.models.guardrail_report import (
    GuardrailFinding, GuardrailReport, GuardrailSeverity
)

class RecommendationGuardrails:
    CAUSAL_PATTERNS = (
        r"\bvocê perdeu porque\b",
        r"\bperdeu porque\b",
        r"\bcausou sua derrota\b",
        r"\bfoi a causa\b",
    )
    TIMING_PATTERNS = (
        r"\b4[- ]?2\b", r"\b4[- ]?1\b", r"\b3[- ]?2\b",
        r"\b5[- ]?1\b", r"\bround\s+\d\b", r"\bestágio\s+\d[- ]\d\b",
    )
    RANK_PATTERNS = (
        r"\bvocê vai subir\b",
        r"\bpronto para subir\b",
        r"\bgarante a subida\b",
    )
    MISSION_PATTERNS = (
        r"\bvocê falhou na missão\b",
        r"\bvocê cumpriu a missão\b",
        r"\bmissão concluída\b",
        r"\bexecutou corretamente a missão\b",
        r"\bexecutou mal a missão\b",
    )
    PRIORITY_PATTERNS = (
        r"\btroque (?:seu )?foco\b",
        r"\bmude (?:seu )?foco\b",
        r"\bnova prioridade\b",
        r"\babandone (?:o|a) (?:foco|missão)\b",
    )
    ABSOLUTE_PATTERNS = (
        r"\bsempre\b", r"\bnunca\b", r"\bcom certeza\b",
        r"\bsem dúvida\b", r"\bobrigatoriamente\b",
    )

    @classmethod
    def validate(cls, *, recommendation, action_signals=None,
                 active_skill_label=None, mission_title=None,
                 direct_evidence_count=0):
        fields = cls._fields(recommendation)
        findings = []
        rules = [
            ("FALSE_CAUSALITY", cls.CAUSAL_PATTERNS, GuardrailSeverity.BLOCK,
             "A recomendação atribui causalidade sem telemetria suficiente."),
            ("UNSUPPORTED_TIMING", cls.TIMING_PATTERNS, GuardrailSeverity.BLOCK,
             "A recomendação usa timing específico não sustentado pelos dados."),
            ("RANK_UP_PREDICTION", cls.RANK_PATTERNS, GuardrailSeverity.BLOCK,
             "A recomendação prevê promoção/rank up."),
            ("UNAUTHORIZED_PRIORITY_CHANGE", cls.PRIORITY_PATTERNS, GuardrailSeverity.BLOCK,
             "A recomendação tenta trocar foco/prioridade sem autorização."),
            ("ABSOLUTE_LANGUAGE", cls.ABSOLUTE_PATTERNS, GuardrailSeverity.WARNING,
             "A recomendação usa linguagem absoluta."),
        ]
        for field_name, text in fields.items():
            for rule_id, patterns, severity, message in rules:
                hit = cls._hit(text, patterns)
                if hit:
                    findings.append(GuardrailFinding(rule_id, severity, message, field_name, hit))
            if direct_evidence_count <= 0:
                hit = cls._hit(text, cls.MISSION_PATTERNS)
                if hit:
                    findings.append(GuardrailFinding(
                        "UNSUPPORTED_MISSION_JUDGMENT", GuardrailSeverity.BLOCK,
                        "A recomendação julga a missão sem evidência direta suficiente.",
                        field_name, hit
                    ))
        secondary = getattr(recommendation, "secondary_actions", ()) or ()
        if len(secondary) > 2:
            findings.append(GuardrailFinding(
                "TOO_MANY_ACTIONS", GuardrailSeverity.WARNING,
                "Há ações secundárias demais para uma orientação focada.",
                "secondary_actions"
            ))
        preserve = str(getattr(recommendation, "preserve", "") or "").lower()
        all_text = " ".join(fields.values()).lower()
        if preserve == "economia" and (
            "gaste todo" in all_text or "zere seu ouro" in all_text or "sempre role" in all_text
        ):
            findings.append(GuardrailFinding(
                "CONFLICT_WITH_PRESERVED_STRENGTH", GuardrailSeverity.WARNING,
                "A recomendação pode entrar em conflito com a força de Economia.",
                "recommendation"
            ))
        blocks = sum(x.severity == GuardrailSeverity.BLOCK for x in findings)
        warnings = sum(x.severity == GuardrailSeverity.WARNING for x in findings)
        infos = sum(x.severity == GuardrailSeverity.INFO for x in findings)
        return GuardrailReport(
            passed=blocks == 0,
            findings=tuple(findings),
            blocked_count=blocks,
            warning_count=warnings,
            info_count=infos,
        )

    @staticmethod
    def _fields(rec):
        fields = {
            "title": str(getattr(rec, "title", "") or ""),
            "recommendation": str(getattr(rec, "recommendation", "") or ""),
            "why_now": str(getattr(rec, "why_now", "") or ""),
            "competitive_context": str(getattr(rec, "competitive_context", "") or ""),
            "training_context": str(getattr(rec, "training_context", "") or ""),
            "preserve": str(getattr(rec, "preserve", "") or ""),
        }
        for i, item in enumerate(getattr(rec, "secondary_actions", ()) or (), 1):
            fields[f"secondary_action_{i}"] = str(item or "")
        return fields

    @staticmethod
    def _hit(text, patterns):
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(0)
        return None
