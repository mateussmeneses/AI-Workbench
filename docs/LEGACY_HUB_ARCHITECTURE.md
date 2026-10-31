# Arquitetura

```text
browser_profiles (Chrome/Edge/Brave) ─┐
bookmark_export_html (Firefox/outros) ├─> IMPORT (somente leitura) ─> NORMALIZE ─> DEDUP ─> ENRICH
GitHub API via gh auth ───────────────┘                                      │
                                                                            ▼
                                             catalog.json v0.1 / SQLite FTS5 futuro
                                                                            │
                            ┌───────────────────────────────────────────────┼───────────────────┐
                            ▼                                               ▼                   ▼
                        CLASSIFY                                         SEARCH             REVIEW QUEUE
                            │
                    repository signals + current task
                            │
                            ▼
                    RANK / RECOMMEND
                            │
                            ▼
                ATTACH (preview + idempotent)
                            │
               .ai-workbench/RESOURCES.md (gitignored)
               .ai-workbench/attachment.json (gitignored)
               AGENTS.md managed note (no personal URLs)
                            │
           Codex / Hermes / OpenClaude adapters (opt-in)
```

## Separação de interesses

- **Source connectors:** browser sources e `gh api`; não confundir favorites do navegador com GitHub starred. O Hub não presume acesso direto ao Chrome nem a credenciais da nuvem.
- **Canonical store:** JSON v0.1 em `~/.ai-workbench-hub/catalog.json`; futura migração versionada para SQLite + FTS5 com backups.
- **Classifier:** regras JSON auditáveis primeiro; eventual modelo local para dúvida. `confidence` com justificativa; resource type separado de domain.
- **Project analyzer:** arquivos de build, extensões, testes e caminhos observáveis; incorporar instruções do usuário e contexto de tarefa sem enviar catálogo completo ao LLM.
- **Attachment adapter:** gerar seleção local, não ativar dependências antes de uma política de revisão.
- **Runtime adapters:** `~/.codex/AGENTS.md` e `.agents/skills`, `.openclaude/skills`, Hermes skills trust. Nenhuma configuração global é tocada automaticamente.
- **MCP facade:** futuro servidor somente leitura sobre índice, opcional por workspace.

## Privacidade

O índice pode conter links privados, fragmentos de buscas e endpoints corporativos. Guardar no home do usuário e jamais enviar o catálogo completo para modelos de nuvem. Recursos locais do projeto são excluídos do Git. Não copiar arquivos de cookies ou senhas do perfil de navegador.

## Threat model mínimo

- Bookmark malicioso contendo prompt injection: tratado como dado e apenas exibido.
- README de repositório sugerindo instalar comandos: nunca executado automaticamente.
- URL com token em query: identificar/redigir antes de logs e de exportações.
- Dependência de repositório arquivado/desatualizado: indicar estado, não presumir qualidade.
- Distribuição indiscriminada de skills/MCPs: seleção por perfil, opt-in e revisão.
- Editar `AGENTS.md` com instruções existentes: marcador gerenciado, backup e testes de idempotência.

## Integração ao starter anterior

`../ai-workbench` é a fonte canônica de `skills/`, `agents/`, `profiles/` e `mcp/`. Hub é o catálogo e roteador. Não copiar/mesclar cegamente os dois: consumir índice de perfis e delegar instalação de skills existentes após inspeção.
