
# Cada linha de código deve aproximar o jogador da sua próxima vitória


# 🧠 TFT Insight AI - Architecture Guidelines

> **A missão do TFT Insight AI não é mostrar estatísticas.**
>
> Nossa missão é ajudar o jogador a tomar melhores decisões na próxima partida.

---

# Filosofia

O TFT Insight AI é dividido em duas grandes camadas.

```
Interface
        ↓
Performance Engine
        ↓
Dados
```

Cada camada possui uma responsabilidade única.

---

# Nossa missão

Todo desenvolvimento deve responder uma pergunta.

> **"Isso ajuda o jogador a tomar uma decisão melhor na próxima partida?"**

Se a resposta for **não**, provavelmente essa funcionalidade não pertence ao produto.

---

# Princípios

## 1. O usuário nunca deve precisar interpretar dezenas de métricas.

O sistema interpreta os dados.

O jogador recebe decisões.

---

## 2. A IA não toma decisões.

A IA apenas explica.

O algoritmo sempre decide primeiro.

```
Métricas

↓

Performance Engine

↓

Prioridades

↓

Coach AI

↓

Texto para o jogador
```

Nunca o contrário.

---

## 3. Todo cálculo pertence ao Performance Engine.

A Interface nunca calcula.

Exemplo:

❌ Errado

```python
score = economy * 0.25
```

Dentro da Home.

✔ Correto

```python
score = PerformanceEngine.calculate(...)
```

---

## 4. Toda tela apenas exibe dados.

Views não possuem regras de negócio.

Elas apenas renderizam modelos.

```
Performance

↓

HomeData

↓

Home
```

---

## 5. Models nunca calculam.

Models representam dados.

Nunca regras.

✔ Correto

```python
Priority

Player

Benchmark

Performance
```

❌ Errado

```python
Priority.calculate()

Player.get_score()
```

---

## 6. Services nunca implementam regras de negócio.

Services apenas coordenam o fluxo.

✔ Correto

```python
metrics = ...

performance = PerformanceEngine.calculate(metrics)

return performance
```

❌ Errado

```python
if economy < 40:
    score -= 20
```

Essa lógica pertence ao Engine.

---

## 7. O Performance Engine nunca conhece a Interface.

Ele não sabe que existe:

- Streamlit
- Dashboard
- Sidebar
- Botões
- Home

Ele apenas recebe dados.

```
Player Metrics

↓

Performance Engine

↓

Performance
```

---

## 8. O Performance Engine nunca conhece a Riot API.

Ele recebe objetos internos do projeto.

Nunca respostas da Riot.

```
Riot API

↓

Transformers

↓

Player Metrics

↓

Performance Engine
```

---

## 9. O código deve ser reutilizável.

O Engine deve funcionar igualmente em:

- Streamlit
- Desktop
- Mobile
- API
- CLI

Nenhuma regra deve depender da interface.

---

## 10. Toda funcionalidade deve ser reutilizável.

Antes de criar um novo arquivo, responda:

> **Esse código calcula alguma coisa ou apenas transporta dados?**

Se calcula:

```
performance_engine/
```

Se apenas organiza informações:

```
models/
services/
views/
ui/
```

---

# Organização do projeto

```
Riot API

↓

Transformers

↓

Player Metrics

↓

Performance Engine

↓

Performance

↓

Priorities

↓

Coach

↓

HomeData

↓

UI
```

---

# Performance Engine

O Performance Engine é o cérebro do projeto.

Ele é responsável por transformar métricas em decisões.

Nunca em interfaces.

---

# Coach AI

O Coach AI nunca cria regras.

Ele interpreta resultados produzidos pelo Performance Engine.

Exemplo

Entrada

```
Economia

71

Benchmark

93

Impacto

+12
```

Saída

> Você está chegando ao nível 8 com menos ouro que o Benchmark. Priorize preservar economia até o Stage 4.

---

# Filosofia de Produto

O TFT Insight AI não compete mostrando mais gráficos.

Ele compete respondendo uma pergunta.

> **"O que eu devo fazer agora para ganhar mais LP?"**

Todo desenvolvimento deve aproximar o usuário dessa resposta.

---

# Regra de Ouro

Sempre que houver dúvida sobre onde colocar um código, faça apenas uma pergunta:

> **Esse código calcula alguma coisa ou apenas transporta dados?**

Essa pergunta define onde o código pertence.

---

# Nossa visão

Não estamos construindo um dashboard.

Estamos construindo um treinador.


# Checklist antes de criar um novo arquivo

Antes de adicionar qualquer código, responda às seguintes perguntas:

- [ ] Esse código calcula alguma coisa?
- [ ] Esse código apenas transporta dados?
- [ ] Esse código depende da Interface?
- [ ] Esse código pode ser reutilizado em outro lugar?
- [ ] Isso ajuda o jogador a tomar uma decisão melhor na próxima partida?

Se alguma resposta indicar que o código está na camada errada, reavalie sua implementação.

---

# Processo de Desenvolvimento

Antes de criar qualquer classe, módulo ou funcionalidade, responda às perguntas abaixo.

## 1. Qual é a responsabilidade deste módulo?

Cada módulo deve possuir uma única responsabilidade.

Exemplo:

Responsabilidade:

> Transformar métricas em uma avaliação de performance.

---

## 2. Qual é a entrada?

Defina claramente quais objetos este módulo recebe.

Exemplo:

Entrada:

- PlayerMetrics
- Benchmark

---

## 3. Qual é a saída?

Defina claramente o que será retornado.

Exemplo:

Saída:

- Performance

---

## 4. Esse código calcula alguma coisa ou apenas transporta dados?

Se calcula:

→ Performance Engine

Se apenas organiza ou transporta informações:

→ Models / Services / UI

---

## 5. Esse código pode ser reutilizado?

Se a resposta for não, reavalie a implementação.

Todo componente deve ser reutilizável em diferentes interfaces:

- Streamlit
- Desktop
- API
- Mobile

---

## 6. Esse código depende da Interface?

Se depender de:

- Streamlit
- Botões
- Sidebar
- Componentes visuais

ele não pertence ao Performance Engine.

---

## 7. Isso ajuda o jogador a tomar uma decisão melhor na próxima partida?

Essa é a principal pergunta do projeto.

Se a resposta for não, provavelmente essa funcionalidade não agrega valor ao produto.

Nosso objetivo não é mostrar mais estatísticas.

Nosso objetivo é transformar dados em decisões.

---

# Checklist antes de escrever código

Antes de implementar qualquer funcionalidade, confirme:

- [ ] A responsabilidade do módulo está claramente definida.
- [ ] A entrada está definida.
- [ ] A saída está definida.
- [ ] O módulo possui apenas uma responsabilidade.
- [ ] O código está na camada correta.
- [ ] O componente pode ser reutilizado.
- [ ] O componente não depende da Interface.
- [ ] Essa funcionalidade ajuda o jogador a tomar uma decisão melhor.

Somente depois desse checklist o desenvolvimento deve começar.

---

# Princípio da Evolução

Não escrevemos código para resolver apenas o problema de hoje.

Escrevemos código que permita evoluir o produto amanhã.

Sempre que existir mais de uma solução possível, escolha aquela que:

- seja mais fácil de manter;
- seja mais fácil de testar;
- reduza o acoplamento entre módulos;
- permita adicionar novas funcionalidades sem reescrever as existentes.

O objetivo não é apenas fazer funcionar.

O objetivo é construir uma base sólida para o crescimento do TFT Insight AI.