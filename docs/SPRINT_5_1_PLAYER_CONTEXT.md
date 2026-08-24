# Sprint 5.1 — Player Context Engine

Princípio: **Analyze once, navigate everywhere.**

A sessão mantém Riot ID, tag, região, quantidade de partidas, última análise,
último benchmark e horário da última atualização.

O histórico guarda apenas os cinco jogadores recentes, sem duplicar relatórios
completos, evitando crescimento desnecessário do `st.session_state`.
