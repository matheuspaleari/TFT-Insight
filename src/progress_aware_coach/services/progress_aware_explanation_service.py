from __future__ import annotations

class ProgressAwareExplanationService:
    """Fase 13.6: explicação determinística e auditável da reação ao progresso."""

    @classmethod
    def build(cls, *, context: dict, strategy: dict, adaptation: dict) -> dict:
        skill = str(context.get("skill_id", "skill"))
        signal = str(context.get("signal", "WATCH"))
        snapshots = int(context.get("snapshot_count", 0) or 0)
        delta = context.get("delta")
        delta_text = f"{float(delta):+.2f}" if isinstance(delta, (int, float)) else "não disponível"

        if signal == "WATCH":
            title = "Mudança observada, reação ainda em espera"
            summary = f"{skill} mudou {delta_text} pontos entre os registros disponíveis, mas existem apenas {snapshots} snapshots avaliáveis. O coach registra o sinal sem tratar a mudança como tendência persistente."
        elif signal == "REGRESSION":
            title = "Queda persistente pede reforço"
            summary = f"{skill} apresenta uma sequência de queda com evidência suficiente para adaptar a abordagem. A prioridade é preservada e o treino recebe reforço, não uma troca automática de Skill."
        elif signal == "IMPROVEMENT":
            title = "Melhora consistente reconhecida"
            summary = f"{skill} apresenta melhora em sequência. O coach reconhece o progresso e prepara uma possível progressão, sem avançar a dificuldade por conta própria."
        else:
            title = "Histórico sem direção dominante"
            summary = f"Os snapshots de {skill} não mostram uma direção consistente suficiente para mudar a abordagem agora."

        return {
            "title": title,
            "summary": summary,
            "next_step": adaptation.get("instruction", ""),
            "evidence": [
                f"Snapshots avaliáveis: {snapshots}",
                f"Delta acumulado: {delta_text}",
                f"Sinal longitudinal: {signal}",
                f"Confiança: {context.get('confidence', 'LOW')}",
            ],
            "limitations": [
                "O histórico longitudinal não escolhe outra Skill.",
                "A adaptação não altera missão ou dificuldade automaticamente.",
                "Mudança observada não é tratada como causalidade.",
            ],
            "source": "deterministic",
        }
