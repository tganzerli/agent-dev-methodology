<!--
  Instala como: {{project}}_wiki/work/relay/_templates/peer-message.md
  Ver .claude/skills/peer-relay/SKILL.md e kit:modules/peer-relay/README.md.

  Estende `message.md` (intra-team). Mesmos msg_role, mesma tabela de asks com IDs
  estáveis, mesmo round log. Três acréscimos, e todos existem porque o leitor está
  em OUTRO repositório: frontmatter com dois espaços de nomes, uma seção de
  Orientação, e um terceiro closing ask.

  Copie para {{project}}_wiki/work/relay/{YYYY-MM-DD}_{slug}.md e preencha os {...}.
  Mantenha a sub-seção do msg_role que está autorando; apague as outras.
  Prosa em {{KNOWLEDGE_LANG}}.
-->
---
title: {título}
type: relay
direction: outbound            # outbound (autoramos) | inbound (recebemos)
peer: {nome no registro}       # ex.: tcc — precisa existir em .agents/peers.md
from_agent: {modelo/role}      # ex.: opus-5/backend-foundations
to_agent: {modelo/role | any}
msg_role: request              # note | request | response | handoff | conflict
status: sent                   # sent | read | acked | resolved | superseded
updated: {YYYY-MM-DD}
summary: Uma frase — o que esta mensagem coordena.
work_refs: []                  # NOSSOS work_ids / branches
peer_work_refs: []             # work_ids DELES — espaço de nomes separado, não misture
related: []
---

# {título}

**De:** {from_agent} · `{{project}}`  **Para:** {to_agent} · `{peer}`

> **Citação qualificada por repo.** Todo `file:line` carrega prefixo: `{peer}:caminho/arquivo:linha`
> para o repositório do leitor, `{{project}}:caminho/arquivo:linha` para o nosso. Um `file:line` sem
> prefixo é erro de formato — o mesmo caminho existe nos dois repositórios.
>
> **Assimetria deliberada.** Citações ao repo **do leitor** são reference-first puras (ele abre).
> Citações ao **nosso** repo vêm com resumo inline suficiente — ele *pode* abrir, mas está em outro
> checkout e **não vai**; a citação fica como proveniência.
>
> **Claim-state com origem:** `✅ landed (repo@branch)` · `⚠ in-flight (repo@branch)` · `🔒 intent`.
>
> **`[[wikilinks]]` só para páginas do repo do leitor** — vaults são distintos; um wikilink nosso
> vira link morto no Obsidian dele.

## 1. Contexto

> Por que esta mensagem existe. 1–3 parágrafos. Vale para todo `msg_role`.

## 2. Orientação

> **Seção exclusiva deste módulo.** Onde, **no repositório do leitor**, ficam as coisas que esta
> mensagem discute. Sem isto, uma rodada inteira se gasta em "onde isso fica?".
>
> Liste os pontos de ancoragem no repo dele — arquivos, páginas de wiki, work_ids, benchmarks —
> com o prefixo dele. Se a mensagem toca um escopo travado, diga qual e aponte o board.

- `{peer}:{caminho}` — {o que é, por que importa aqui}
- `{peer}:{caminho}` — {…}
- Board consultado: `{peer}:{wiki}/work/relay/_board.md` — {lock relevante, ou "nenhum lock ativo colide"}

## 3. Corpo

> Mantenha a sub-seção do `msg_role`; apague as demais.

**Se `note`** — o que mudou / o que observar, com prefixo de repo e claim-state.

**Se `handoff`** — **Estado no handoff** (plano, execução, branch, último commit; tag `⚠ in-flight` o não-commitado) · **O que falta** (aponte os passos do plano, não os re-liste) · **Landmines** (lição cara; se durável, gradue para página de conhecimento) · **Ownership**.

**Se `conflict`** — **Colisão** (o escopo compartilhado, com prefixo de repo dos dois lados) · **Posições** (state-tagged, com origem) · **Resolução proposta**.

**Se `request` / `response`** — prosa de enquadramento que os asks da §4 precisem.

## 4. Open asks

> `request` levanta; `response` reusa os **MESMOS** IDs — nunca renumera. Rodada nova acrescenta
> `A7`, `A8`… e re-statusa os antigos (`open → answered → resolved`; `superseded` com ponteiro).

| ID | Bloqueante | Ask | Status |
|---|---|---|---|
| A1 | 🔴 | {o que precisamos que o outro agente faça/decida} | open |
| A2 | ⚪ | {…} | open |

## 5. Closing asks

> **Três**, não dois. Os dois primeiros são herdados do `intra-team`; o terceiro existe porque, entre
> repositórios, não há lugar compartilhado óbvio para a resposta.

1. **Reconhecer e responder in-thread**, keyed aos IDs `A` acima. Não renumerar.
2. **Respeitar o gate compartilhado** — nada de código antes de plano aprovado do seu lado; consultar
   o board antes de tocar escopo compartilhado.
3. **Depositar a resposta em `{{ABS_PATH_TO_THIS_REPO}}/{{project}}_wiki/work/relay/`**,
   com `direction: inbound`, `peer: {{project}}` e os mesmos IDs de ask. Caminho absoluto porque
   estamos em repositórios diferentes na mesma máquina.

## Round log

- **R1 — {YYYY-MM-DD}:** enviado. Bloqueantes: {A1, …}.
