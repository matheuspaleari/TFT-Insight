from src.post_match.models.post_match_interpretation import PostMatchInterpretation, PostMatchInterpretationItem

class PostMatchInterpretationService:
    @staticmethod
    def _band_phrase(c):
        if c is None or c.baseline_mean is None:
            return "Ainda não há histórico suficiente para comparação pessoal."
        band = getattr(c.band, "value", str(c.band))
        word = {"ABOVE":"acima", "BELOW":"abaixo", "WITHIN":"próximo"}.get(band, "próximo")
        return f"Isso ficou {word} do seu padrão recente (média {c.baseline_mean:.2f})."

    @classmethod
    def interpret(cls, *, analysis, baseline):
        comps = {x.metric_id:x for x in baseline.comparisons}
        evid = {x.signal_id:x for x in analysis.evidence}
        focus = next((x for x in analysis.evidence if x.relation == "focus"), None)

        if focus:
            metric = {"final_level":"level","gold_left":"gold_left","board_pressure":"total_damage_to_players"}.get(focus.signal_id, focus.signal_id)
            personal = cls._band_phrase(comps.get(metric))
            focus_text = (
                f"{focus.label}: {focus.value}. {personal} "
                f"Esse dado tem relação com {analysis.active_skill_label or 'o foco atual'}, "
                "mas mede apenas o resultado final dessa dimensão; não mostra se a decisão "
                "treinada foi executada no momento e contexto corretos."
            )
        else:
            focus_text = "Não há sinal observável suficiente para interpretar diretamente o foco atual."

        placement = comps.get("placement")
        damage = comps.get("total_damage_to_players")
        pb = getattr(getattr(placement,"band",None),"value",None)
        db = getattr(getattr(damage,"band",None),"value",None)
        if pb == "BELOW" and db == "BELOW":
            overview = (
                "Esta partida ficou abaixo do seu padrão recente em resultado e pressão sobre "
                "o lobby. Isso descreve o que aconteceu, mas não identifica sozinho qual decisão "
                "causou a queda de desempenho."
            )
        else:
            overview = (
                "A partida foi comparada com o seu próprio histórico recente. As diferenças "
                "servem para contextualizar o jogo, não para substituir a avaliação da missão."
            )

        contexts = []
        for sid, title, metric, base in [
            ("placement","Resultado da partida","placement",90),
            ("board_pressure","Pressão sobre o lobby","total_damage_to_players",80),
            ("gold_left","Recursos no fim da partida","gold_left",60),
            ("contestacao","Contestação do lobby",None,50),
        ]:
            e = evid.get(sid)
            if not e: continue
            c = comps.get(metric) if metric else None
            personal = cls._band_phrase(c) if c else ""
            if sid == "placement":
                txt=f"Você terminou em {e.value}. {personal} A colocação descreve o resultado, mas não prova sucesso ou falha na missão."
            elif sid == "board_pressure":
                txt=f"{e.value}. {personal} Isso ajuda a entender sua pressão no lobby, sem atribuir o resultado a uma decisão específica."
            elif sid == "gold_left":
                txt=f"Você terminou com {e.value} de ouro. {personal} Isso não diz sozinho se gastar ou guardar seria correto."
            else:
                txt=f"{e.value}. A contestação ajuda a explicar o ambiente da partida, mas não substitui o foco oficial de treino."
            band=getattr(getattr(c,"band",None),"value",None)
            importance=base + (10 if band in ("ABOVE","BELOW") else 0)
            contexts.append(PostMatchInterpretationItem(sid,title,txt,importance,getattr(e.evidence_class,"value",str(e.evidence_class)),band))
        contexts=tuple(sorted(contexts,key=lambda x:x.importance,reverse=True)[:2])

        labels=[x.label for x in analysis.unavailable_evidence]
        missing=(
            "Para avaliar diretamente a missão, ainda faltam sinais como "
            + (", ".join(labels[:-1]) + f" e {labels[-1]}" if len(labels)>1 else (labels[0] if labels else "a linha do tempo da decisão"))
            + ". Esses dados não estão disponíveis na telemetria atual, então o sistema não deve inventá-los."
        )
        conclusion=(
            "A partida acrescenta contexto sobre o seu desempenho, mas ainda não fornece "
            "evidência direta suficiente para julgar a execução da missão. O foco de treino permanece inalterado."
        )
        return PostMatchInterpretation(
            headline=f"Leitura da partida {analysis.match_id}",
            overview=overview,
            focus_reading=focus_text,
            context_readings=contexts,
            missing_information=missing,
            conclusion=conclusion,
        )
