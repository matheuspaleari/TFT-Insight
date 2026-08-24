from __future__ import annotations

from typing import Final


COACH_MESSAGE_LIBRARY: Final[dict[str, dict[str, tuple[str, ...]]]] = {
    "top4_rate": {
        "priority_title": (
            "Transforme mais partidas em bons resultados",
            "Faça a consistência aparecer mais vezes",
            "Seu próximo salto passa por mais Top 4",
        ),
        "priority_body": (
            (
                "A frequência de Top 4 é hoje uma das maiores distâncias para a "
                "referência escolhida. Seu foco de treino deve ser aumentar a "
                "regularidade dos bons resultados, em vez de depender apenas das "
                "partidas em que tudo encaixa."
            ),
            (
                "O padrão do próximo nível aparece com mais frequência em Top 4. "
                "Para evoluir, o objetivo agora é transformar mais partidas comuns "
                "em resultados sólidos e repetíveis."
            ),
            (
                "Seu teto pode até produzir boas partidas, mas a evolução de elo "
                "vem quando bons resultados deixam de ser exceção. Trabalhe para "
                "tornar o Top 4 mais frequente na sua amostra."
            ),
        ),
        "strength_title": (
            "Sua consistência de Top 4 já é uma força",
            "Você já converte bem partidas em Top 4",
        ),
        "strength_body": (
            (
                "Sua frequência de Top 4 já está na ou acima da referência. "
                "Mantenha esse padrão e direcione a maior parte do treino para "
                "as métricas que ainda estão segurando sua progressão."
            ),
            (
                "Você já apresenta uma regularidade competitiva de Top 4. "
                "Não transforme isso em prioridade agora; preserve esse ponto "
                "forte enquanto trabalha nos gaps principais."
            ),
        ),
    },
    "win_rate": {
        "priority_title": (
            "Converta melhor suas melhores partidas",
            "Transforme vantagem em mais vitórias",
            "Seu teto precisa aparecer mais vezes",
        ),
        "priority_body": (
            (
                "Sua taxa de vitória está abaixo da referência. Isso não significa "
                "que toda partida precisa ser jogada por primeiro lugar, mas mostra "
                "que suas melhores partidas ainda podem gerar mais resultados máximos."
            ),
            (
                "Você já chega a partidas competitivas, mas ainda existe espaço para "
                "converter mais delas em vitória. Esse é um sinal de teto: quando a "
                "partida estiver favorável, seu resultado final ainda pode crescer."
            ),
            (
                "O próximo nível vence uma parcela maior das partidas. Trate isso "
                "como um objetivo de conversão das suas melhores situações, sem "
                "sacrificar a consistência geral."
            ),
        ),
        "strength_title": (
            "Você já converte bem suas melhores partidas",
            "Sua taxa de vitória é um ponto forte",
        ),
        "strength_body": (
            (
                "Sua taxa de vitória já está na ou acima da referência. Esse é um "
                "bom sinal de teto competitivo; mantenha essa capacidade enquanto "
                "prioriza os gaps mais relevantes."
            ),
            (
                "Quando suas partidas encaixam, você consegue transformar vantagem "
                "em resultado. Preserve esse ponto forte e concentre o treino na "
                "regularidade das demais métricas."
            ),
        ),
    },
    "average_placement": {
        "priority_title": (
            "Reduza o peso das partidas ruins",
            "Sua média precisa ficar mais estável",
            "Proteja melhor sua colocação ao longo da amostra",
        ),
        "priority_body": (
            (
                "Sua colocação média está atrás da referência. O ganho mais importante "
                "aqui é reduzir o impacto das partidas que terminam muito abaixo do seu "
                "padrão, tornando a amostra mais estável."
            ),
            (
                "A diferença de colocação média indica que suas partidas ruins ainda "
                "custam bastante no conjunto. O objetivo de treino é fazer o resultado "
                "médio subir pela consistência, não apenas por partidas excepcionais."
            ),
            (
                "Seu próximo passo é diminuir a distância entre as partidas boas e as "
                "partidas ruins. Uma média mais forte costuma nascer de menos resultados "
                "muito baixos ao longo da amostra."
            ),
        ),
        "strength_title": (
            "Sua colocação média já é competitiva",
            "Você já sustenta uma média forte",
        ),
        "strength_body": (
            (
                "Sua colocação média está na ou acima da referência. Isso indica uma "
                "boa base de consistência; mantenha esse padrão enquanto direciona o "
                "treino para outros gaps."
            ),
            (
                "A sua média de colocação já acompanha bem o benchmark. Preserve essa "
                "regularidade e evite gastar foco de treino em uma métrica que já está "
                "respondendo."
            ),
        ),
    },
    "average_level": {
        "priority_title": (
            "Revise seu ritmo de progressão",
            "Seu ritmo médio de nível está atrás da referência",
            "A progressão do seu board merece atenção",
        ),
        "priority_body": (
            (
                "Seu nível médio está abaixo da referência. Isso não significa "
                "simplesmente 'upar mais': use o dado como um sinal para revisar o "
                "equilíbrio entre estabilizar o jogo atual e preservar recursos para "
                "continuar progredindo."
            ),
            (
                "O benchmark termina as partidas em um nível médio maior. Considere "
                "essa diferença como um indicador do seu ritmo de progressão ao longo "
                "das partidas, sem transformar a métrica em uma regra isolada."
            ),
        ),
        "strength_title": (
            "Seu ritmo de progressão já é uma força",
            "Você já acompanha bem o nível da referência",
        ),
        "strength_body": (
            (
                "Seu nível médio já está na ou acima da referência. Isso sugere que "
                "seu ritmo de progressão não precisa ser prioridade neste momento; "
                "mantenha o padrão e foque nos gaps de resultado."
            ),
            (
                "Você já alcança um nível médio competitivo. Preserve esse ritmo e "
                "direcione o treino para as métricas que ainda não acompanham a "
                "referência."
            ),
        ),
    },
    "average_damage_to_players": {
        "priority_title": (
            "Seu board precisa gerar mais pressão",
            "A força média das suas partidas pode crescer",
            "Transforme sua progressão em mais impacto",
        ),
        "priority_body": (
            (
                "Seu dano médio aos jogadores está abaixo da referência. O dado sugere "
                "que, no conjunto das partidas, seu board exerce menos pressão sobre o "
                "lobby do que o padrão comparado."
            ),
            (
                "Existe um gap de impacto: sua amostra causa menos dano médio aos "
                "adversários. Use isso como sinal de que a força que você constrói ao "
                "longo da partida ainda pode aparecer com mais frequência."
            ),
        ),
        "strength_title": (
            "Você já exerce boa pressão no lobby",
            "Seu dano médio é um ponto forte",
        ),
        "strength_body": (
            (
                "Seu dano médio aos jogadores já está na ou acima da referência. "
                "Isso indica boa pressão ao longo das partidas; mantenha essa força "
                "enquanto trabalha nas métricas de resultado."
            ),
            (
                "Seu board já produz impacto competitivo na amostra. Preserve esse "
                "padrão e concentre o treino onde a diferença para a referência é maior."
            ),
        ),
    },
    "placement_standard_deviation": {
        "priority_title": (
            "Diminua a oscilação entre partidas",
            "Sua consistência ainda pode melhorar",
            "Faça seu desempenho variar menos",
        ),
        "priority_body": (
            (
                "Sua variação de colocação está pior que a referência. O principal "
                "objetivo aqui é reduzir extremos e tornar o desempenho mais previsível "
                "ao longo de várias partidas."
            ),
            (
                "Os resultados ainda oscilam mais do que o benchmark. Trabalhar "
                "regularidade tende a fazer seu desempenho real aparecer com mais "
                "frequência, inclusive quando a partida não começa ideal."
            ),
        ),
        "strength_title": (
            "Sua regularidade já é competitiva",
            "Você mantém uma boa estabilidade entre partidas",
        ),
        "strength_body": (
            (
                "Sua variação de colocação já acompanha ou supera a referência. "
                "Consistência não precisa ser o foco principal agora; preserve esse "
                "padrão."
            ),
            (
                "Você apresenta boa estabilidade entre partidas. Esse é um ponto forte "
                "importante para evolução de elo e deve ser mantido enquanto os outros "
                "gaps são trabalhados."
            ),
        ),
    },
}


GENERIC_MESSAGES: Final[dict[str, tuple[str, ...]]] = {
    "priority_title": (
        "Este é o seu principal foco agora",
        "Aqui está o maior espaço de evolução",
    ),
    "priority_body": (
        (
            "Essa é uma das maiores diferenças para a referência selecionada. "
            "Use a métrica como foco de treino nas próximas partidas e acompanhe "
            "se o gap diminui quando a amostra crescer."
        ),
        (
            "O benchmark mostra uma diferença relevante nessa dimensão. "
            "Trabalhe esse ponto primeiro e use as próximas análises para medir "
            "se a distância está realmente diminuindo."
        ),
    ),
    "strength_title": (
        "Isso já é um ponto forte",
        "Mantenha esse padrão",
    ),
    "strength_body": (
        (
            "Você já está na ou acima da referência nessa dimensão. Preserve "
            "esse padrão e concentre o treino nos gaps que têm maior impacto."
        ),
        (
            "Essa métrica já responde bem contra o benchmark. Não precisa ser "
            "prioridade agora; mantenha a consistência enquanto trabalha no restante."
        ),
    ),
}
