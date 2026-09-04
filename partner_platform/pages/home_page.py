from __future__ import annotations

import re

import streamlit as st

from partner_platform.components import (
    executive_card,
    insight_banner,
    section_header,
)


def _render_html(markup: str) -> None:
    """Renderiza HTML da Home sem depender do parser Markdown."""
    if hasattr(st, "html"):
        st.html(markup)
        return

    compact = re.sub(
        r">\s+<",
        "><",
        markup.strip(),
    )
    st.markdown(
        compact,
        unsafe_allow_html=True,
    )


def render(
    *,
    context,
    api_client,
    analytics,
) -> None:
    del api_client, analytics

    _render_html("""
        <div class="tft-home-hero">
            <div class="tft-home-kicker">TFT INSIGHT</div>
            <h1>Aprenda a pensar como um Challenger.</h1>
            <p>
                Transforme seu histórico de partidas em evidências claras,
                prioridades e decisões melhores para o próximo lobby.
            </p>
        </div>
        """)

    insight_banner(
        eyebrow="Seu histórico vira contexto",
        title="Não é só um painel de números.",
        description=(
            "O TFT Insight organiza padrões das suas partidas e coloca o Coach "
            "na frente das métricas para ajudar você a entender onde prestar "
            "atenção na próxima partida."
        ),
        tone="positive",
    )

    if st.button(
        "Analisar meu Riot ID",
        type="primary",
        width="stretch",
    ):
        st.session_state["_tft_navigation_target"] = "Benchmark"
        st.rerun()

    section_header(
        "O que o TFT Insight analisa",
        subtitle=(
            "Quatro leituras especializadas trabalham sobre o seu histórico "
            "recente sem inventar informações que a telemetria não registra."
        ),
    )

    _render_html("""
        <div class="tft-home-intelligence-grid">

            <div class="tft-home-intelligence-card">
                <div class="tft-home-intelligence-icon">◇</div>
                <div class="tft-home-intelligence-kicker">COMPOSIÇÕES</div>
                <div class="tft-home-intelligence-title">
                    Entenda seus padrões de estrutura
                </div>
                <div class="tft-home-intelligence-text">
                    Veja quando você está explorando bastante, repetindo padrões
                    ou encontrando composições que funcionam melhor no seu histórico.
                </div>
                <div class="tft-home-intelligence-proof">
                    Diversidade · repetição · composição mais usada · melhor resultado
                </div>
            </div>

            <div class="tft-home-intelligence-card">
                <div class="tft-home-intelligence-icon">◎</div>
                <div class="tft-home-intelligence-kicker">CONTESTAÇÃO</div>
                <div class="tft-home-intelligence-title">
                    Saiba onde a disputa merece atenção
                </div>
                <div class="tft-home-intelligence-text">
                    Identifique quando carries, unidades importantes e traits
                    aparecem compartilhados com outros boards do lobby.
                </div>
                <div class="tft-home-intelligence-proof">
                    Carry contestado · pressão recorrente · adversários no carry
                </div>
            </div>

            <div class="tft-home-intelligence-card">
                <div class="tft-home-intelligence-icon">↗</div>
                <div class="tft-home-intelligence-kicker">ECONOMIA</div>
                <div class="tft-home-intelligence-title">
                    Entenda seu ritmo de progressão
                </div>
                <div class="tft-home-intelligence-text">
                    Acompanhe nível, ouro final e padrões de progressão para entender
                    como sua economia costuma terminar nas partidas analisadas.
                </div>
                <div class="tft-home-intelligence-proof">
                    Nível médio · ouro final · Fast 8 · Fast 9
                </div>
            </div>

            <div class="tft-home-intelligence-card">
                <div class="tft-home-intelligence-icon">◆</div>
                <div class="tft-home-intelligence-kicker">CARRIES + ITENS</div>
                <div class="tft-home-intelligence-title">
                    Reveja suas escolhas recorrentes
                </div>
                <div class="tft-home-intelligence-text">
                    Veja quais carries e itemizações aparecem com mais frequência
                    e como esses padrões se comportam no seu histórico recente.
                </div>
                <div class="tft-home-intelligence-proof">
                    Carry mais usado · itens recorrentes · frequência · resultados
                </div>
            </div>

        </div>
        """)

    section_header(
        "Como funciona",
        subtitle=(
            "Do Riot ID à próxima decisão: cada etapa acrescenta contexto "
            "sem pular das métricas direto para uma conclusão."
        ),
    )

    _render_html("""
        <div class="tft-home-journey">
            <div class="tft-home-step">
                <div class="tft-home-step-number">1</div>
                <div class="tft-home-step-content">
                    <div class="tft-home-step-kicker">ENTRADA</div>
                    <div class="tft-home-step-title">Riot ID</div>
                    <div class="tft-home-step-text">
                        Você informa o jogador e quantas partidas quer analisar.
                    </div>
                </div>
            </div>

            <div class="tft-home-connector">→</div>

            <div class="tft-home-step">
                <div class="tft-home-step-number">2</div>
                <div class="tft-home-step-content">
                    <div class="tft-home-step-kicker">CONTEXTO</div>
                    <div class="tft-home-step-title">Histórico recente</div>
                    <div class="tft-home-step-text">
                        O TFT Insight organiza as partidas e identifica o contexto competitivo.
                    </div>
                </div>
            </div>

            <div class="tft-home-connector">→</div>

            <div class="tft-home-step">
                <div class="tft-home-step-number">3</div>
                <div class="tft-home-step-content">
                    <div class="tft-home-step-kicker">LEITURA</div>
                    <div class="tft-home-step-title">4 inteligências</div>
                    <div class="tft-home-step-text">
                        Composições, contestação, economia e carries + itens encontram padrões.
                    </div>
                </div>
            </div>

            <div class="tft-home-connector">→</div>

            <div class="tft-home-step tft-home-step-coach">
                <div class="tft-home-step-number">4</div>
                <div class="tft-home-step-content">
                    <div class="tft-home-step-kicker">PRIORIDADE</div>
                    <div class="tft-home-step-title">Coach</div>
                    <div class="tft-home-step-text">
                        As evidências são organizadas em uma prioridade clara para o próximo lobby.
                    </div>
                </div>
            </div>
        </div>

        <div class="tft-home-outcome">
            <div class="tft-home-outcome-kicker">RESULTADO</div>
            <div class="tft-home-outcome-title">
                Você não recebe só mais métricas — recebe contexto para decidir melhor.
            </div>
        </div>
        """)

    section_header(
        "O diferencial do Coach",
        subtitle=(
            "Métricas mostram sinais. O Coach organiza esses sinais e destaca "
            "o que merece atenção primeiro."
        ),
    )

    _render_html("""
        <div class="tft-home-coach">

            <div class="tft-home-coach-copy">
                <div class="tft-home-coach-kicker">COACH TFT INSIGHT</div>
                <div class="tft-home-coach-title">
                    Números mostram o que aconteceu.
                    <span>O Coach ajuda a escolher onde olhar primeiro.</span>
                </div>

                <div class="tft-home-coach-text">
                    Seu histórico pode trazer muitos sinais ao mesmo tempo.
                    O TFT Insight organiza as evidências já calculadas e transforma
                    esse conjunto em uma prioridade de leitura para a próxima partida.
                </div>

                <div class="tft-home-coach-note">
                    O Coach não inventa eventos de partida e não afirma conhecer
                    a jogada perfeita. A recomendação permanece limitada ao que
                    os dados analisados realmente sustentam.
                </div>
            </div>

            <div class="tft-home-coach-flow">

                <div class="tft-home-coach-step">
                    <div class="tft-home-coach-step-number">1</div>
                    <div>
                        <div class="tft-home-coach-step-title">Detecta padrões</div>
                        <div class="tft-home-coach-step-text">
                            Usa os sinais produzidos pelas inteligências do histórico.
                        </div>
                    </div>
                </div>

                <div class="tft-home-coach-step">
                    <div class="tft-home-coach-step-number">2</div>
                    <div>
                        <div class="tft-home-coach-step-title">Compara evidências</div>
                        <div class="tft-home-coach-step-text">
                            Considera força, recorrência e contexto dos sinais disponíveis.
                        </div>
                    </div>
                </div>

                <div class="tft-home-coach-step">
                    <div class="tft-home-coach-step-number">3</div>
                    <div>
                        <div class="tft-home-coach-step-title">Prioriza o maior gap</div>
                        <div class="tft-home-coach-step-text">
                            Coloca a principal oportunidade antes do restante do relatório.
                        </div>
                    </div>
                </div>

                <div class="tft-home-coach-step">
                    <div class="tft-home-coach-step-number">4</div>
                    <div>
                        <div class="tft-home-coach-step-title">Explica o motivo</div>
                        <div class="tft-home-coach-step-text">
                            Mostra por que aquela prioridade merece atenção.
                        </div>
                    </div>
                </div>

                <div class="tft-home-coach-step">
                    <div class="tft-home-coach-step-number">5</div>
                    <div>
                        <div class="tft-home-coach-step-title">Preserva limites</div>
                        <div class="tft-home-coach-step-text">
                            Mantém incertezas e limitações visíveis ao jogador.
                        </div>
                    </div>
                </div>

            </div>

        </div>
        """)

    section_header(
        "Confiança sem promessas exageradas",
        subtitle=(
            "O TFT Insight separa o que os dados sustentam do que a telemetria "
            "não permite afirmar."
        ),
    )

    _render_html("""
        <div class="tft-home-trust">
            <div class="tft-home-trust-panel tft-home-trust-positive">
                <div class="tft-home-trust-kicker">O QUE OS DADOS SUSTENTAM</div>
                <div class="tft-home-trust-title">Leituras baseadas no seu histórico</div>

                <div class="tft-home-trust-item">
                    <span class="tft-home-trust-mark">✓</span>
                    <span>Encontrar padrões recorrentes nas partidas analisadas.</span>
                </div>
                <div class="tft-home-trust-item">
                    <span class="tft-home-trust-mark">✓</span>
                    <span>Comparar sinais e evidências entre partidas.</span>
                </div>
                <div class="tft-home-trust-item">
                    <span class="tft-home-trust-mark">✓</span>
                    <span>Priorizar oportunidades sustentadas pelos módulos de análise.</span>
                </div>
                <div class="tft-home-trust-item">
                    <span class="tft-home-trust-mark">✓</span>
                    <span>Explicar quais evidências levaram à leitura apresentada.</span>
                </div>
            </div>

            <div class="tft-home-trust-panel tft-home-trust-limit">
                <div class="tft-home-trust-kicker">O QUE O PRODUTO NÃO AFIRMA</div>
                <div class="tft-home-trust-title">Limites continuam visíveis</div>

                <div class="tft-home-trust-item">
                    <span class="tft-home-trust-mark">×</span>
                    <span>Conhecer todas as decisões tomadas durante cada rodada.</span>
                </div>
                <div class="tft-home-trust-item">
                    <span class="tft-home-trust-mark">×</span>
                    <span>Provar causalidade apenas porque dois sinais aparecem juntos.</span>
                </div>
                <div class="tft-home-trust-item">
                    <span class="tft-home-trust-mark">×</span>
                    <span>Prever uma jogada perfeita para o próximo lobby.</span>
                </div>
                <div class="tft-home-trust-item">
                    <span class="tft-home-trust-mark">×</span>
                    <span>Reconstruir contexto que não está disponível na telemetria.</span>
                </div>
            </div>
        </div>

        <div class="tft-home-trust-footer">
            <div class="tft-home-trust-footer-kicker">TRANSPARÊNCIA</div>
            <div>
                Quando a amostra é pequena ou a evidência é limitada, a leitura
                deve permanecer exploratória — não virar uma certeza artificial.
            </div>
        </div>
        """)

    with st.expander(
        "Como interpretar as recomendações",
        expanded=False,
    ):
        st.write(
            "O TFT Insight descreve padrões observados no histórico e usa esses "
            "sinais para orientar atenção e revisão. Ele não observa todas as "
            "decisões tomadas durante cada rodada e não trata associação histórica "
            "como prova de causa."
        )

    _render_html("""
        <div class="tft-home-final-cta">
            <div class="tft-home-final-cta-copy">
                <div class="tft-home-final-cta-kicker">PRÓXIMA PARTIDA</div>
                <div class="tft-home-final-cta-title">
                    Pronto para entender melhor suas partidas?
                </div>
                <div class="tft-home-final-cta-text">
                    Use seu Riot ID para transformar o histórico recente em contexto,
                    prioridades e evidências para revisar antes do próximo lobby.
                </div>
            </div>
        </div>
        """)

    if st.button(
        "Analisar meu Riot ID",
        type="primary",
        width="stretch",
        key="tft_home_final_cta",
    ):
        st.session_state["_tft_navigation_target"] = "Benchmark"
        st.rerun()

    st.caption(
        "TFT Insight · Aprenda a pensar como um Challenger."
    )
