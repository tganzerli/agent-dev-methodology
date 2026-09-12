# Conventions extension — peer-relay module

> **Installer:** append the section below (everything between the two `⟪…⟫` markers) into
> `{{project}}_wiki/_meta/conventions.md`, as a new top-level section **after** the intra-team
> section (it declares inheritance from it, so order matters). Do **not** create a separate file in
> the target project. Remove the `⟪…⟫` markers when pasting.
>
> This extension is only installed when the **peer-relay module** is active (INSTALL.md §5-ter).
> It requires the **intra-team** extension to be installed first — it inherits that vocabulary
> instead of redefining it.

---

⟪ BEGIN drop-in section — paste into {{project}}_wiki/_meta/conventions.md ⟫

## Peer-relay frontmatter (agente↔agente, repositórios distintos na mesma máquina)

Mensagens trocadas com o agente de **outro projeto** que consegue ler o nosso repositório mas não o compartilha. Vivem em `work/relay/`, ao lado das mensagens `intra-team`, e usam a skill `peer-relay`. Os peers são declarados em `.agents/peers.md`.

**Herança, para não duplicar.** Este módulo **reusa integralmente** o frontmatter e o vocabulário do §"Intra-team frontmatter" acima — `type: relay`, `direction`, `from_agent`, `to_agent`, `msg_role` (`note|request|response|handoff|conflict`), `status` (`sent|read|acked|resolved|superseded`) e `work_refs`. Não os redefina aqui. Só o delta segue.

### Campos adicionais

```yaml
peer: {peer}                   # nome do peer no registro .agents/peers.md — obrigatório
peer_work_refs: []             # work_ids DO PEER. Separado de work_refs (os nossos),
                               # porque há dois espaços de nomes e os dois usam
                               # o formato YYYY-MM-DD_slug — a colisão é questão de tempo.
```

### Regra que rege: reference-first **qualificado**

Terceiro valor do eixo que separa os outros dois módulos. `cross-team` assume que o leitor **não tem acesso** ao nosso código (self-contained); `intra-team` assume que ele **compartilha** o repositório (reference-first). Aqui o leitor **consegue ler, mas não compartilha** — e as duas regras falham:

| | Citação ao repo **do leitor** | Citação ao **nosso** repo |
|---|---|---|
| Forma | `peer:caminho/arquivo:linha` | `{{project}}:caminho/arquivo:linha` |
| Conteúdo | reference-first puro — ele abre, não re-cole | reference-first **com resumo inline suficiente** — ele *pode* abrir, mas está em outro checkout e **não vai** |
| Wikilink | `[[página]]` resolve | **não use** — vaults distintos, vira link morto |

🔒 **Um `file:line` sem prefixo de repo é erro de formato**, não questão de estilo: o mesmo caminho relativo existe nos dois repositórios e significa coisas diferentes.

### Claim-state com origem

O `intra-team` tagueia por estado (`✅ landed` / `⚠ in-flight` / `🔒 intent`). Entre repositórios isso é insuficiente — `landed` **onde**? Todo tag carrega origem:

- `✅ landed ({{project}}@main)` — commitado numa branch que o leitor consegue buscar.
- `⚠ in-flight ({{project}}@<work-branch>)` — existe, mas não na branch que ele lê.
- `🔒 intent` — planejado, não iniciado. Sem origem, porque não há o que apontar.

### Onde vivem

Mensagens → `work/relay/{YYYY-MM-DD}_{slug}.md`, template `_templates/peer-message.md`. O board é **compartilhado** com o `intra-team` (`work/relay/_board.md`): locks cujo escopo vive no repo de um peer levam o prefixo dele na coluna Escopo.

Como as mensagens `intra-team`, ficam no layer `work/` mas **não** entram em `_meta/index.md` nem no `work/_index.md` gerado — `work-index`, `work-find` e `work-audit` varrem apenas `tasks`/`plans`/`executions`.

⟪ END drop-in section ⟫
