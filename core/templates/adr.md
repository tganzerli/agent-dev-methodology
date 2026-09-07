<!--
  Instala como: {{project}}_wiki/decisions/_templates/adr.md

  Template de ADR **comum**. Para mudança de contrato versionado (API pública,
  schema de banco, protocolo de fio, schema de evento, ABI de FFI) use
  `adr-contract.md`, que o `contract_change_rule.md` exige.

  Prosa em pt-BR; chaves e valores de frontmatter em inglês.
  Apague estas linhas-guia ao salvar. Todo `{...}` é campo do autor.
-->
---
title: {YYYY-MM-DD} — {a decisão, em uma linha}
type: adr
work_id: {YYYY-MM-DD_slug}
scope:
  apps: []
  packages: []
status: accepted            # proposed | accepted | superseded | deprecated
updated: {YYYY-MM-DD}
revisit_when: "{gatilho OBSERVÁVEL — a fase ou o trabalho que produz a evidência que falta.
                Ex.: 'primeira implementação de um repositório (Fase 2)'.
                NUNCA 'quando fizer sentido'. Vazio só se nada puder refinar esta decisão.}"
supersedes: []
superseded_by: ""
sources: []
code_refs: []               # arquivos que a decisão governa; vazio se ainda não há código
related: []
---

# {YYYY-MM-DD} — {a decisão, em uma linha}

## Contexto

{Qual é a força que obriga a decidir agora, e o que acontece se não se decidir. Restrições que valem: requisito de produto, invariante do repositório, dependência externa, decisão anterior que esta consome.

**Nenhuma decisão do `docs/_legacy/` é herdada** — if the project archived a previous methodology, say so here and do not inherit from it. O legado pode ser citado como contexto histórico; o argumento é reconstruído aqui.}

## Decisão

{A decisão, enunciada de forma que dê para verificar se foi seguida. Não "vamos usar uma arquitetura modular", e sim a regra que um revisor consegue aplicar a um PR.}

## Alternativas descartadas

> 🔒 **Obrigatório.** Um ADR que só afirma a escolha não cumpre o critério: sem as alternativas, ninguém sabe se o espaço foi explorado, e a decisão não pode ser reaberta com informação nova.

| Alternativa | Por que foi descartada | O que a traria de volta |
|---|---|---|
| {…} | {…} | {o fato observável que mudaria o veredito} |

## Consequências

{O que passa a ser verdade — inclusive o que fica pior. Um ADR que só lista benefícios está escondendo o custo, e o custo é o que a próxima pessoa precisa saber.}

- **Positivas:** {…}
- **Custos aceitos:** {…}
- **Novas restrições sobre trabalho futuro:** {…}

## Como esta decisão é policiada

{Como se descobre que a decisão foi violada — teste, lint, revisão, ou nada.

Este bloco existe por evidência: in a real Dart backend, 68 of 76 domain files imported the framework although the project's own `ARCHITECTURE.md` claimed purity (cite the analysis that measured it). **Convenção sem mecanismo não sobrevive.** Se a resposta honesta for "nada", escreva "nada" — é informação, e é um débito nomeado.}

## Revisão prevista

> 🔒 **Esta seção declara a PERGUNTA, não a resposta.** Preenchê-la com o que se acha que vai
> acontecer é adivinhar de novo, com mais palavras. Ela se escreve **agora**, enquanto se sabe o que
> não se sabe — depois da implementação ninguém lembra qual era a dúvida.
>
> O gate 🔒 "ADRs affected" do `mandatory_planning_rule.md` §4.2 obriga o plano que implementar esta
> área a dizer se este ADR sai **confirmado**, **refinado** ou **superado**.

**Gatilho:** {o mesmo de `revisit_when`, em prosa}

**O que a implementação deve ensinar:** {a pergunta concreta que hoje não tem resposta e terá}

**O que se espera:** {confirmar / refinar / a hipótese específica que pode cair}

## Decisões que esta abre ou fecha

- **Fecha:** {perguntas que deixam de estar em aberto}
- **Abre:** {perguntas novas, com a fase do roadmap em que serão respondidas}

## Referências

- {`file:line` com prefixo de repo quando for outro repositório: `peer:` prefixes from `.agents/peers.md`}
