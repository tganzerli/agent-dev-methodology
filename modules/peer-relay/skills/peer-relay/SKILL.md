---
name: peer-relay
description: Coordenar com o agente de OUTRO projeto no mesmo computador — repositórios distintos que conseguem ler um ao outro. Cobre absorção (orientar-se no repo do peer sem varrê-lo), envio de mensagem à caixa de entrada dele, leitura da nossa caixa, e o board compartilhado. Use quando precisar pedir, responder, avisar ou transferir trabalho para um projeto declarado em .agents/peers.md — por exemplo o projeto do TCC. Não use para agentes deste mesmo repositório (é `intra-team`) nem para times sem acesso ao nosso código (é `cross-team-handoff`).
argument-hint: "[absorb <peer> | send <peer> <slug> | read <peer> | board]"
---

# Peer-relay — coordenação entre projetos na mesma máquina

Terceiro valor de um eixo que os outros dois módulos tratam como binário. `modules/intra-team/README.md` o enuncia: *"they differ on one axis — does the reader share your repository?"*

| | `cross-team` | `intra-team` | **`peer-relay`** |
|---|---|---|---|
| O leitor **compartilha** seu repo | não | sim | **não** |
| O leitor **consegue ler** seu repo | não | sim | **sim** |
| Regra | self-contained | reference-first | **reference-first qualificado** |

Ele **importa a maquinaria do `intra-team`** — os cinco `msg_role` (`note`/`request`/`response`/`handoff`/`conflict`), a tabela de asks com IDs estáveis, o round log, o board. Leia `.claude/skills/intra-team/SKILL.md` para todos eles; **não são repetidos aqui.** O que segue é só o delta.

## Pré-requisitos

- `.agents/peers.md` declara o peer: caminho, prefixo, política de escrita, caixa de entrada, pontos de entrada de absorção.
- `{{project}}_wiki/work/relay/` existe, com `_board.md` e `_templates/peer-message.md`.
- Prosa em {{KNOWLEDGE_LANG}}.

## Delta 1 — a regra de citação

O motivo de o módulo existir. Num universo de dois repositórios, `router.dart:9` existe **nos dois** e significa coisas diferentes.

1. 🔒 **Toda citação de arquivo carrega prefixo de repo.** `tcc:dart/lib/src/decoder/_decoder.dart:56`, `{{project}}:packages/domain/lib/src/value/enums.dart:1-3`. O prefixo vem de `.agents/peers.md`. Um `file:line` sem prefixo é **erro de formato**, não estilo.
2. **Citação ao repo do leitor: reference-first puro.** Ele abre o arquivo. Não re-cole.
3. **Citação ao nosso repo: reference-first *com resumo inline suficiente*.** Ele *pode* abrir, mas está em outro checkout com outro contexto carregado e **não vai**. A afirmação se sustenta sozinha no corpo; a citação fica como proveniência verificável. É o meio-termo que nenhum dos outros dois módulos oferece — e é o erro mais fácil de cometer, porque "reference-first" convida a só apontar.
4. **`[[wikilinks]]` só para páginas do repo do leitor.** Vaults são distintos: um wikilink para o nosso vault vira link morto no Obsidian dele. Para páginas nossas, caminho de arquivo com prefixo.
5. **`work_id` é namespaced na travessia:** `{{project}}:2026-09-06_backend-foundations-track`. Os dois projetos usam `YYYY-MM-DD_slug`; a colisão é questão de tempo.
6. **Claim-state ganha um eixo.** O `intra-team` distingue `✅ landed` / `⚠ in-flight` / `🔒 intent`. Aqui `landed` sozinho não diz nada — landed **onde**? Formato: `✅ landed ({{project}}@main)`, `⚠ in-flight ({{project}}@docs/…__knowledge)`.

## Delta 2 — os quatro fluxos

### `absorb <peer>` · autônomo

Orienta você no repo do peer **lendo apenas os pontos de entrada declarados**, na ordem em que estão, parando quando a pergunta em mãos estiver respondida.

🔒 **Nunca varra o repositório do peer.** O registro existe para evitar isso: um `grep -r` no repo alheio queima contexto e produz um mapa que o `overview.md` dele já dá em uma página.

🔒 **Não faça pattern-match em nome de seção.** Um peer pode escrever o conhecimento noutro idioma —
`## Em andamento` em vez de `## In progress`. Um recorte ancorado no cabeçalho errado devolve vazio, e
vazio lê-se como "não há nada", que é uma conclusão falsa e silenciosa. **Liste os cabeçalhos primeiro**
(`grep -n '^#'`) e recorte pelo que existe.

Leia também as **peculiaridades** do peer no registro antes de concluir qualquer coisa — elas são exatamente os pontos em que um índice mente (um `_index.md` desatualizado, uma tag local, um lock morto).

Saída: um resumo de estado — o que o projeto é, o que está em voo, o que está travado, e o que na sua pergunta continua sem resposta.

### `send <peer> <slug>` · **GATE HUMANO DUPLO**

Redige a mensagem em `{{project}}_wiki/work/relay/{YYYY-MM-DD}_{slug}.md` (template `peer-message.md`) e a **entrega** na caixa de entrada do peer.

🔒 **Dois gates, não um.** (a) o humano aprova o **texto**; (b) o humano aprova a **escrita no repositório do outro projeto**. São decisões diferentes: a segunda é irreversível do nosso lado, porque não temos permissão de commit lá para desfazer.

🔒 **Antes de redigir, leia o board do peer** (`<peer>:…/work/relay/_board.md`) e o nosso. Escrever sobre um escopo travado sem reconhecer o lock é exatamente o atropelo que o board existe para evitar.

🔒 **Respeite a política de escrita do registro.** Se ela diz `work/relay/` apenas, é `work/relay/` apenas — nenhum arquivo fora dali, nenhuma branch, nenhum commit.

Depois de entregue: append em `{{project}}_wiki/_meta/log.md` (`## [YYYY-MM-DD] peer-relay | {slug} | to {peer}`) e, se a mensagem cria lock ou acordo, atualize o board.

### `read <peer>` · autônomo

Lê `{{project}}_wiki/work/relay/` procurando `direction: inbound` daquele peer, e resume o que exige resposta — priorizando asks com flag 🔴.

Uma mensagem lida vira `status: read`; respondida, `answered`. **Não** feche um ask sem que a resposta exista de fato.

### `board` · gate humano

Mantém `{{project}}_wiki/work/relay/_board.md`. Locks cujo escopo vive no repo do peer levam o **prefixo dele** na coluna Escopo (`tcc:dart/lib/`).

Um lock aqui é sinal **social**, não trava de sistema de arquivos — e entre repositórios é ainda mais frágil, porque o outro agente pode nem ter olhado. Ao travar escopo que atravessa a fronteira, **diga isso na mensagem**; não confie no board sozinho.

## Delta 3 — o que a mensagem carrega a mais

O template `peer-message.md` estende o `message.md` do `intra-team` em três pontos:

- **Frontmatter:** `peer` (nome no registro), `peer_work_refs` (work_ids do lado deles) e `work_refs` (os nossos) — **separados**, porque há dois espaços de nomes.
- **Seção "Orientação"**, logo após o Contexto: onde, **no repo do leitor**, ficam as coisas que a mensagem discute. É o que evita uma rodada inteira gasta em "onde isso fica?".
- **Terceiro closing ask:** onde depositar a resposta (nossa caixa, caminho absoluto). Diferente do `intra-team`, não existe um lugar compartilhado óbvio.

## Anti-padrões

- ❌ `file:line` sem prefixo de repo.
- ❌ `[[wikilink]]` apontando para o nosso vault numa mensagem que sai daqui.
- ❌ Varrer o repositório do peer em vez de usar os pontos de entrada.
- ❌ Escrever no repo do peer sem o segundo gate, ou fora da política do registro.
- ❌ Só apontar `{{project}}:arquivo:linha` sem o resumo inline — o leitor não vai abrir.
- ❌ Usar este módulo para um agente **deste** repo (é `intra-team`) ou para um time sem acesso ao nosso código (é `cross-team-handoff`).
- ❌ Marcar um acordo como `A` no board antes do ack real do outro lado.

## Referências

- `.agents/peers.md` — o registro.
- `.claude/skills/intra-team/SKILL.md` — a maquinaria herdada.
- `.claude/skills/cross-team-handoff/SKILL.md` — o caso sem acesso ao código.
- `{{project}}_wiki/_meta/conventions.md` §"Peer-relay frontmatter".
