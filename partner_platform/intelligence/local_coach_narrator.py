from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
from typing import Any

import httpx


DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2:3b"


SYSTEM_PROMPT = """Você é o coach narrador local do TFT Insight.

Toda análise, cálculo e conclusão já foi produzida pelo TFT Insight.
Você não analisa partidas por conta própria. Você transforma os fatos
recebidos em UMA única conversa de coach, natural, específica e útil.

O payload pode conter:
- prioridade estratégica;
- ajustes estratégicos;
- pontos fortes de composição, contestação e economia;
- métricas de comparação com benchmark.

OBJETIVO:
Faça o jogador sentir que um coach revisou o conjunto das partidas, e não
que está lendo cards ou uma lista de métricas.

REGRAS DE CONTEÚDO:
1. Use somente fatos, números, conclusões e recomendações recebidos.
2. Não faça cálculos novos e não altere números.
3. Não invente acontecimentos de partida.
4. Não invente itens, augments, stages, rolls, streaks, posicionamento,
   scouting ou decisões que não estejam no payload.
5. Não transforme frequência em causalidade.
6. Só diga que contestação piorou resultados quando o payload sustentar isso.
7. Não diga que o jogador força composição se o payload não sustentar isso.
8. Se flexibilidade/composição for uma força, preserve essa conclusão.
9. Se economia for uma força, preserve essa conclusão.
10. Não transforme Top 4 em vitória ou primeiro lugar.
11. Não troque colocação média, taxa de vitória ou qualquer outra métrica.
12. Não contradiga a prioridade determinada pelo TFT Insight.

REGRAS DE INTERPRETAÇÃO:
13. Números não possuem significado implícito. Não classifique um valor como
    alto, baixo, forte, fraco, significativo, crítico, excepcional, irrelevante
    ou semelhante sem que essa interpretação apareça no conteúdo recebido.
14. Se o contexto trouxer um label ou uma interpretação explícita, você pode
    reescrevê-la de forma natural, preservando exatamente a intensidade.
15. Não aumente nem reduza a força de uma conclusão. "Relevante" não vira
    "crítico"; "leve" não vira "significativo"; "forte" não vira "excepcional".
16. Frases amigáveis e floreios são permitidos quando não alteram o significado
    aprovado pelo TFT Insight.

REGRAS DE NARRATIVA:
13. Produza UMA narrativa integrada; não escreva um relatório por categoria.
14. Comece pelo ponto que mais merece atenção.
15. Explique por que ele merece atenção usando os números relevantes.
16. Em seguida, conecte naturalmente os pontos fortes que o jogador deve preservar.
17. Use benchmark somente quando ele acrescentar contexto útil à leitura.
18. Não tente mencionar todas as métricas recebidas.
19. Evite frases genéricas como "continue melhorando", "mantenha o foco" ou
    "trabalhe nos gaps" quando não estiverem acompanhadas de algo específico.
20. Pode usar linguagem amigável como "aqui eu ficaria de olho",
    "isso é um bom sinal", "eu não mexeria muito nisso agora",
    "vale prestar atenção", desde que não adicione fatos.
21. Não repita a mesma recomendação com palavras diferentes.
22. Não use títulos, listas, bullets, markdown, emojis ou tabelas.
23. Não mencione engines, payload, regras, IA, Ollama ou processo interno.
24. Responda somente em português do Brasil.
25. Produza de 2 a 4 parágrafos curtos, com 1 a 3 frases por parágrafo.
26. Não gere parágrafos vazios.
27. Quando receber competitive_spectrum, trate-o somente como contexto de posição
    dentro do grupo competitivo. Entrada, Consolidação, Avançado e Transição
    descrevem posição relativa de elo; não significam qualidade absoluta do jogo.
28. Nunca diga que estar em determinada faixa significa estar pronto ou não para subir.
29. Nunca transforme quantidade de métricas acima/abaixo do grupo em requisito de promoção.
30. Não diga que o jogador precisa ficar acima do grupo em todas as métricas.
31. Separe mentalmente duas coisas: posição competitiva (elo) e perfil recente
    (métricas). Uma contextualiza a outra, mas não prova causalidade.
32. Prefira a expressão "grupo competitivo" ao falar com o jogador. Evite
    "benchmark" e "referência" quando uma frase mais humana for possível.
33. Priorize uma recomendação acionável para a próxima partida. Detalhes de
    evidência podem aparecer depois; não comece despejando todas as métricas.
34. Não repita a posição do Spectrum em vários parágrafos. Use-a no máximo
    uma vez para contextualizar a recomendação.
35. Não explique a arquitetura interna do TFT Insight ao jogador.
36. Nunca use a palavra interna "contest" na resposta ao jogador. Em português,
    o termo correto desta ferramenta é "contestação".
37. Organize a recomendação em três ideias quando houver dados suficientes:
    problema observado, foco de treino e ponto forte a preservar.
38. O Competitive Spectrum pode contextualizar o motivo e o nível de exigência
    da explicação, mas nunca pode substituir Learning Priority na escolha do foco.
39. Existe somente UMA prioridade oficial de treino por vez: a primeira mensagem
    com role="priority" fornecida pelo TFT Insight. Nunca chame qualquer outro
    assunto de "outra prioridade", "segunda prioridade", "mais uma prioridade"
    ou "prioridade importante".
40. Depois da prioridade oficial, trate contestação, economia, composição e
    demais assuntos apenas como "sinal complementar", "observação complementar"
    ou "ponto a observar", conforme o conteúdo recebido.
41. Termine sempre a resposta com uma frase completa. Se estiver perto do limite,
    omita detalhes secundários em vez de começar uma frase que não conseguirá concluir.

ESTRUTURA IDEAL:
Parágrafo 1: prioridade oficial de treino + por que ela foi escolhida.
Parágrafo 2: ação prática da missão atual para a próxima partida.
Parágrafo 3: no máximo um ou dois sinais complementares realmente úteis.
Parágrafo 4 opcional: ponto forte aprovado pelo contexto, somente quando existir.

O texto final deve soar como uma conversa contínua. Não escreva expressões
como "na categoria composição", "sobre economia" ou "em contestação" apenas
para separar assuntos. Faça as transições naturalmente.

Se não for possível melhorar a fluidez sem adicionar informação nova,
preserve as mensagens-base quase literalmente.
"""


@dataclass(frozen=True)
class CoachNarrative:
    text: str
    source: str
    model: str | None = None
    diagnostic: str | None = None


class LocalCoachNarrator:
    """
    Narrador local opcional do TFT Insight.

    V9: o modelo pode florear o tom, mas não pode interpretar sozinho
    intensidade, relevância ou significado dos números. Essas classificações
    passam a vir explicitamente do contexto determinístico do TFT Insight.

    O motor analítico e o Coach Message Engine continuam sendo a fonte
    da verdade. O modelo local recebe somente mensagens-base aprovadas
    e pode apenas conectá-las em uma narrativa mais natural.

    Variáveis de ambiente:
      TFT_INSIGHT_LOCAL_AI_ENABLED=true
      TFT_INSIGHT_LOCAL_AI_MODEL=llama3.2:3b
      TFT_INSIGHT_OLLAMA_URL=http://localhost:11434
      TFT_INSIGHT_LOCAL_AI_TIMEOUT=45
      TFT_INSIGHT_LOCAL_AI_DEBUG=false
    """

    _FORBIDDEN_GENERIC_PATTERNS = (
        r"\ba prioridade principal precisa permanecer primeiro\b",
        r"\bo próximo ajuste vem depois\b",
        r"\bo ponto forte vem por último\b",
        r"\bmensagens-base\b",
        r"\bfonte de verdade\b",
        r"\bsua função é\b",
        r"\bregras obrigatórias\b",
    )

    _FORBIDDEN_TFT_INVENTIONS = (
        "roll",
        "rolar",
        "reroll",
        "scouting",
        "scout",
        "augment",
        "aumento",
        "itemização",
        "itemizacao",
        "posicionamento",
        "stage",
        "estágio",
        "estagio",
        "streak",
        "win streak",
        "lose streak",
        "economia",
        "juros",
        "ouro",
        "loja",
        "composição",
        "composicao",
        "carregar item",
        "carry",
        "frontline",
    )

    def __init__(
        self,
        *,
        enabled: bool = False,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_OLLAMA_URL,
        timeout_seconds: float = 45.0,
    ) -> None:
        self.enabled = enabled
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(
        cls,
    ) -> "LocalCoachNarrator":
        enabled_raw = os.getenv(
            "TFT_INSIGHT_LOCAL_AI_ENABLED",
            "false",
        ).strip().lower()

        enabled = enabled_raw in {
            "1",
            "true",
            "yes",
            "on",
        }

        model = os.getenv(
            "TFT_INSIGHT_LOCAL_AI_MODEL",
            DEFAULT_MODEL,
        ).strip() or DEFAULT_MODEL

        base_url = os.getenv(
            "TFT_INSIGHT_OLLAMA_URL",
            DEFAULT_OLLAMA_URL,
        ).strip() or DEFAULT_OLLAMA_URL

        timeout_raw = os.getenv(
            "TFT_INSIGHT_LOCAL_AI_TIMEOUT",
            "45",
        ).strip()

        try:
            timeout_seconds = float(
                timeout_raw
            )
        except ValueError:
            timeout_seconds = 45.0

        return cls(
            enabled=enabled,
            model=model,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
        )

    def is_available(
        self,
    ) -> bool:
        if not self.enabled:
            return False

        try:
            response = httpx.get(
                f"{self.base_url}/api/tags",
                timeout=min(
                    self.timeout_seconds,
                    3.0,
                ),
            )
            response.raise_for_status()
            return True
        except (
            httpx.HTTPError,
            OSError,
        ):
            return False

    def _model_is_installed(
        self,
    ) -> bool:
        try:
            response = httpx.get(
                f"{self.base_url}/api/tags",
                timeout=min(
                    self.timeout_seconds,
                    5.0,
                ),
            )
            response.raise_for_status()

            payload = response.json()

            installed_names = {
                str(
                    item.get(
                        "name",
                        "",
                    )
                )
                for item in payload.get(
                    "models",
                    [],
                )
            }

            if self.model in installed_names:
                return True

            requested_base = self.model.split(
                ":",
                1,
            )[0]

            return any(
                name.split(
                    ":",
                    1,
                )[0]
                == requested_base
                for name in installed_names
            )
        except (
            httpx.HTTPError,
            OSError,
            ValueError,
            TypeError,
        ):
            return False

    @staticmethod
    def _normalize_text(
        value: str,
    ) -> str:
        value = value.replace(
            "\r\n",
            "\n",
        )

        value = re.sub(
            r"[ \t]+",
            " ",
            value,
        )

        value = re.sub(
            r"\n{3,}",
            "\n\n",
            value,
        )

        return value.strip()

    @staticmethod
    def _base_text(
        messages: list[
            dict[str, Any]
        ],
    ) -> str:
        """
        Fonte textual completa usada apenas para validação de segurança.

        Inclui título, métrica, mensagem e evidências para evitar falsos
        positivos quando o narrador usa um conceito que veio corretamente
        no payload, mas não estava literalmente no campo `message`.
        """
        parts: list[str] = []

        for item in messages:
            parts.extend(
                (
                    str(item.get("metric", "")),
                    str(item.get("metric_label", "")),
                    str(item.get("title", "")),
                    str(item.get("message", "")),
                    json.dumps(
                        item.get("evidence", {}),
                        ensure_ascii=False,
                        default=str,
                    ),
                )
            )

        return " ".join(parts).lower()

    def _contains_forbidden_generic_language(
        self,
        text: str,
    ) -> bool:
        lowered = text.lower()

        return any(
            re.search(
                pattern,
                lowered,
            )
            is not None
            for pattern in self._FORBIDDEN_GENERIC_PATTERNS
        )

    def _contains_unprovided_tft_concepts(
        self,
        text: str,
        messages: list[
            dict[str, Any]
        ],
    ) -> bool:
        lowered = text.lower()
        source_text = self._base_text(
            messages
        )

        for term in self._FORBIDDEN_TFT_INVENTIONS:
            if (
                term in lowered
                and term not in source_text
            ):
                return True

        return False

    @staticmethod
    def _top4_was_changed_into_win(
        text: str,
        messages: list[
            dict[str, Any]
        ],
    ) -> bool:
        source_text = " ".join(
            str(
                item.get(
                    "metric_label",
                    "",
                )
            )
            + " "
            + str(
                item.get(
                    "message",
                    "",
                )
            )
            for item in messages
        ).lower()

        if "top 4" not in source_text:
            return False

        source_has_win_metric = any(
            str(
                item.get(
                    "metric",
                    "",
                )
            )
            == "win_rate"
            for item in messages
        )

        if source_has_win_metric:
            return False

        lowered = text.lower()

        forbidden_win_language = (
            "vitória",
            "vitoria",
            "vitórias",
            "vitorias",
            "top 1",
            "primeiro lugar",
            "ganhar partidas",
            "ganhar mais partidas",
        )

        return any(
            phrase in lowered
            for phrase in forbidden_win_language
        )

    @staticmethod
    def _message_keywords(
        item: dict[str, Any],
    ) -> set[str]:
        """
        Extrai palavras úteis da própria mensagem-base para validar ordem
        sem exigir que o modelo repita literalmente o título ou a métrica.
        """
        source = " ".join(
            (
                str(item.get("metric_label", "")),
                str(item.get("title", "")),
                str(item.get("message", "")),
            )
        ).lower()

        stopwords = {
            "ainda",
            "agora",
            "acima",
            "abaixo",
            "aqui",
            "assim",
            "benchmark",
            "como",
            "contra",
            "deve",
            "essa",
            "esse",
            "esta",
            "este",
            "está",
            "estao",
            "estão",
            "foco",
            "mais",
            "maior",
            "manter",
            "mesmo",
            "muito",
            "nesta",
            "neste",
            "para",
            "pela",
            "pelo",
            "principal",
            "quando",
            "referência",
            "referencia",
            "seu",
            "seus",
            "sua",
            "suas",
            "trabalho",
            "você",
            "voce",
        }

        return {
            token
            for token in re.split(r"\W+", source)
            if (
                len(token) >= 4
                and token not in stopwords
            )
        }

    @classmethod
    def _preserves_priority_order(
        cls,
        text: str,
        messages: list[
            dict[str, Any]
        ],
    ) -> bool:
        """
        Verifica se a prioridade aparece antes dos demais blocos.

        A V3 exigia que o primeiro parágrafo repetisse literalmente palavras
        do título/métrica, o que gerava falsos negativos em paráfrases válidas.
        Aqui comparamos a primeira aparição dos conceitos das mensagens-base.
        """
        priority_messages = [
            item
            for item in messages
            if item.get("role") == "priority"
        ]

        if not priority_messages:
            return True

        normalized = text.lower()

        priority_keywords = cls._message_keywords(
            priority_messages[0]
        )

        if not priority_keywords:
            return True

        priority_positions = [
            normalized.find(keyword)
            for keyword in priority_keywords
            if normalized.find(keyword) >= 0
        ]

        # Se o modelo não repetir literalmente nenhum termo relevante,
        # não reprovamos apenas por isso. Os outros validadores continuam
        # protegendo contra invenções e troca de métricas.
        if not priority_positions:
            return True

        priority_position = min(
            priority_positions
        )

        other_messages = [
            item
            for item in messages
            if item.get("role") in {
                "adjustment",
                "strength",
            }
        ]

        other_positions: list[int] = []

        for item in other_messages:
            for keyword in cls._message_keywords(item):
                position = normalized.find(
                    keyword
                )

                if position >= 0:
                    other_positions.append(
                        position
                    )

        if not other_positions:
            return True

        return priority_position <= min(
            other_positions
        )

    @staticmethod
    def _has_empty_or_useless_paragraphs(
        text: str,
    ) -> bool:
        paragraphs = [
            paragraph.strip()
            for paragraph in text.split("\n\n")
            if paragraph.strip()
        ]

        if not paragraphs:
            return True

        for paragraph in paragraphs:
            words = [
                token
                for token in re.split(r"\W+", paragraph)
                if token
            ]

            # Evita blocos soltos do tipo "Boa!" ou "Vamos nessa."
            if len(words) < 5:
                return True

        return False

    @staticmethod
    def _has_redundant_paragraphs(
        text: str,
    ) -> bool:
        paragraphs = [
            paragraph.strip().lower()
            for paragraph in text.split("\n\n")
            if paragraph.strip()
        ]

        if len(paragraphs) < 2:
            return False

        token_sets = [
            {
                token
                for token in re.split(r"\W+", paragraph)
                if len(token) >= 5
            }
            for paragraph in paragraphs
        ]

        for index, current in enumerate(token_sets):
            if not current:
                continue

            for other in token_sets[index + 1:]:
                if not other:
                    continue

                overlap = len(current & other)
                denominator = min(
                    len(current),
                    len(other),
                )

                if denominator and overlap / denominator >= 0.55:
                    return True

        return False

    @staticmethod
    def _uses_multiple_priority_language(
        text: str,
    ) -> bool:
        """
        Existe uma única prioridade oficial. Outros sinais não podem ser
        promovidos semanticamente a uma segunda prioridade.
        """
        patterns = (
            r"\boutra prioridade\b",
            r"\bsegunda prioridade\b",
            r"\bmais uma prioridade\b",
            r"\bnova prioridade\b",
            r"\bprioridade adicional\b",
            r"\bprioridade importante\b",
        )

        lowered = text.lower()

        return any(
            re.search(
                pattern,
                lowered,
            )
            is not None
            for pattern in patterns
        )

    @staticmethod
    def _looks_truncated(
        text: str,
    ) -> bool:
        """
        Rejeita respostas que terminam no meio de uma frase.

        Se o modelo atingir o limite de tokens, é melhor usar o fallback
        determinístico do que exibir uma sentença cortada ao jogador.
        """
        stripped = text.rstrip()

        if not stripped:
            return True

        if stripped.endswith(
            (
                ".",
                "!",
                "?",
                "…",
                '."',
                '!"',
                '?"',
                ".)",
                "!)",
                "?)",
            )
        ):
            return False

        return True

    def _validate_narrative(
        self,
        text: str,
        messages: list[
            dict[str, Any]
        ],
    ) -> tuple[bool, str | None]:
        """
        Validador V8.

        Rejeita somente problemas que podem introduzir informação errada
        ou conteúdo interno. Questões de estilo (ordem, repetição leve,
        quantidade de parágrafos) viram diagnóstico, não motivo para jogar
        fora uma narrativa factual do modelo.
        """
        text = self._normalize_text(
            text
        )

        if not text:
            return False, "resposta vazia"

        if len(text) > 2200:
            return False, "resposta longa demais"

        if self._contains_forbidden_generic_language(
            text
        ):
            return False, "instrução interna apareceu na resposta"

        if self._contains_unprovided_tft_concepts(
            text,
            messages,
        ):
            return False, "conceito de TFT não fornecido no contexto"

        if self._top4_was_changed_into_win(
            text,
            messages,
        ):
            return False, "Top 4 foi convertido em vitória/Top 1"

        if self._uses_multiple_priority_language(
            text
        ):
            return False, "sinal complementar foi promovido a outra prioridade"

        if self._looks_truncated(
            text
        ):
            return False, "resposta terminou no meio de uma frase"

        # Daqui para baixo são verificações de qualidade, não de segurança.
        warnings: list[str] = []

        if self._has_empty_or_useless_paragraphs(
            text
        ):
            warnings.append(
                "há parágrafo curto demais"
            )

        if not self._preserves_priority_order(
            text,
            messages,
        ):
            warnings.append(
                "prioridade não apareceu primeiro"
            )

        if self._has_redundant_paragraphs(
            text
        ):
            warnings.append(
                "há alguma repetição entre parágrafos"
            )

        paragraph_count = len(
            [
                paragraph
                for paragraph in text.split(
                    "\n\n"
                )
                if paragraph.strip()
            ]
        )

        if paragraph_count > 5:
            warnings.append(
                "mais de 5 parágrafos"
            )

        return (
            True,
            "; ".join(warnings)
            if warnings
            else None,
        )

    @staticmethod
    def _fallback_narrative(
        messages: list[
            dict[str, Any]
        ],
    ) -> str:
        """
        Junta as mensagens-base sem IA.
        Esse texto é usado se o modelo local produzir algo inválido.
        """
        ordered_roles = (
            "priority",
            "adjustment",
            "strength",
        )

        paragraphs: list[str] = []

        for role in ordered_roles:
            for item in messages:
                if item.get(
                    "role"
                ) != role:
                    continue

                title = str(
                    item.get(
                        "title",
                        "",
                    )
                ).strip()

                message = str(
                    item.get(
                        "message",
                        "",
                    )
                ).strip()

                if not message:
                    continue

                if title:
                    paragraphs.append(
                        f"{title}. {message}"
                    )
                else:
                    paragraphs.append(
                        message
                    )

        return "\n\n".join(
            paragraphs[:3]
        ).strip()

    def _user_prompt(
        self,
        messages: list[
            dict[str, Any]
        ],
        *,
        benchmark_name: str,
        competitive_spectrum: dict[str, Any] | None = None,
    ) -> str:
        safe_spectrum = {}

        if isinstance(competitive_spectrum, dict):
            safe_spectrum = {
                "available": bool(
                    competitive_spectrum.get("available")
                ),
                "group_label": competitive_spectrum.get(
                    "group_label"
                ),
                "current_rank": competitive_spectrum.get(
                    "current_rank"
                ),
                "spectrum_band": competitive_spectrum.get(
                    "spectrum_band"
                ),
                "spectrum_percentile": competitive_spectrum.get(
                    "spectrum_percentile"
                ),
                "population_size": competitive_spectrum.get(
                    "population_size"
                ),
                "strengths": competitive_spectrum.get(
                    "strengths",
                    [],
                ),
                "neutral_areas": competitive_spectrum.get(
                    "neutral_areas",
                    [],
                ),
                "attention_areas": competitive_spectrum.get(
                    "attention_areas",
                    [],
                ),
                "limitation": competitive_spectrum.get(
                    "limitation"
                ),
            }

        safe_payload = {
            "grupo_competitivo": benchmark_name,
            "competitive_spectrum": safe_spectrum,
            "messages": messages,
        }

        return (
            "Transforme os fatos abaixo em UMA única conversa de coach. "
            "Não responda item por item e não crie seções por métrica. "
            "Comece pela única prioridade oficial recebida, explique-a com os dados "
            "fornecidos e preserve essa hierarquia até o fim. Qualquer outro assunto "
            "deve ser tratado como sinal complementar, nunca como outra prioridade. "
            "Depois conecte naturalmente somente os pontos fortes explicitamente "
            "recebidos. Se houver competitive_spectrum, use-o apenas para "
            "contextualizar onde o elo está dentro do grupo competitivo. "
            "Não transforme faixa, percentil ou quantidade de métricas em "
            "previsão de subida. Prefira dizer 'grupo competitivo' em vez de "
            "'benchmark' ou 'referência'. "
            "Não invente fatos, não faça novos cálculos e não crie causalidade "
            "que não esteja sustentada. Entregue somente o texto que o jogador "
            "deve ler.\n\n"
            + json.dumps(
                safe_payload,
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )

    @staticmethod
    def _diagnostics_enabled() -> bool:
        value = os.getenv(
            "TFT_INSIGHT_LOCAL_AI_DEBUG",
            "false",
        ).strip().lower()

        return value in {
            "1",
            "true",
            "yes",
            "on",
        }

    def _debug(
        self,
        message: str,
    ) -> None:
        if self._diagnostics_enabled():
            print(
                f"[TFT AI Coach] {message}"
            )

    def narrate(
        self,
        messages: list[
            dict[str, Any]
        ],
        *,
        benchmark_name: str,
        competitive_spectrum: dict[str, Any] | None = None,
    ) -> CoachNarrative | None:
        if (
            not self.enabled
            or not messages
        ):
            return None

        if not self.is_available():
            self._debug(
                "Ollama indisponível em "
                + self.base_url
            )
            return None

        if not self._model_is_installed():
            self._debug(
                "modelo local não encontrado: "
                + self.model
            )
            return None

        request_payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": self._user_prompt(
                        messages,
                        benchmark_name=benchmark_name,
                        competitive_spectrum=competitive_spectrum,
                    ),
                },
            ],
            "options": {
                "temperature": 0.2,
                "top_p": 0.8,
                "repeat_penalty": 1.1,
                "num_predict": 480,
            },
        }

        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json=request_payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()

            payload = response.json()

            content = self._normalize_text(
                str(
                    payload.get(
                        "message",
                        {},
                    ).get(
                        "content",
                        "",
                    )
                )
            )

            is_valid, rejection_reason = self._validate_narrative(
                content,
                messages,
            )

            if is_valid:
                self._debug(
                    "narrativa aceita pelo validador"
                    + (
                        f" com aviso(s): {rejection_reason}"
                        if rejection_reason
                        else ""
                    )
                )
                return CoachNarrative(
                    text=content,
                    source="ollama-local",
                    model=self.model,
                    diagnostic=rejection_reason,
                )

            self._debug(
                "narrativa rejeitada: "
                + str(rejection_reason)
            )

            fallback = self._fallback_narrative(
                messages
            )

            if not fallback:
                return None

            return CoachNarrative(
                text=fallback,
                source="template-fallback",
                model=None,
                diagnostic=rejection_reason,
            )

        except (
            httpx.HTTPError,
            OSError,
            ValueError,
            TypeError,
        ) as exc:
            self._debug(
                "falha no narrador local: "
                + f"{type(exc).__name__}: {exc}"
            )

            fallback = self._fallback_narrative(
                messages
            )

            if not fallback:
                return None

            return CoachNarrative(
                text=fallback,
                source="template-fallback",
                model=None,
                diagnostic="falha ao chamar ou interpretar o narrador local",
            )
