# Roadmap / Entregas verificáveis

## v0.1 — Starter (incluído)
- [x] Projeto Python e CLI inicial (sync, report, attach, doctor).
- [x] Importador Chromium JSON e exportação HTML; GitHub JSON paginado e chamada `gh`.
- [x] Deduplicação simples, classificação por keywords e detecção de perfil.
- [x] Anexo local idempotente com `AGENTS.md` e `.gitignore`.
- [x] Fixtures e testes unitários iniciais, sem fontes pessoais.
- [ ] Testar importação real em Windows 11, em Chrome, Edge e Brave com múltiplos perfis.
- [ ] Confirmar autenticação `gh` e importação paginada real.

## v0.2 — Índice de verdade
- [ ] Corrigir gaps de canonicalização URL, importadores e classificação apontados pela auditoria.
- [ ] Revisão de duplicatas com relatório de origem/folder/profile.
- [ ] Marcar `uncategorized` e fila de revisão para baixa confiança.
- [ ] Redação de segredos nas URLs e proibição de dados pessoais em commit/logs.
- [ ] Camada de storage versionado e backups (SQLite FTS5).
- [ ] Tests dry-run **sem nenhuma escrita** e casos sensíveis.

## v0.3 — Curadoria e ranking
- [ ] Separar `domain` de `resource_type` (skill / agent / MCP / docs / CLI / tutorial).
- [ ] Enriquecer stars com README/topics/language/commit/archived/license conforme limites API.
- [ ] Classificador multicategoria auditável com evidências e sinalizadores de relevância.
- [ ] Command `aiwh search`, `aiwh review`, `aiwh recommend`.

## v0.4 — Acoplamento duradouro
- [ ] `aiwh init --project` e `aiwh attach --task ... --profile ...`.
- [ ] Wrapper para projetos novos (sem hooks globais invasivos).
- [ ] Adapter Codex: instrução global opt-in e perfis de skills via `.agents/skills`.
- [ ] Adapter OpenClaude e Hermes; listar compatibilidade de cada capacidade.
- [ ] Classificar e sugerir recursos do kit `../ai-workbench` com aprovação por ação.

## v0.5 — MCP / UX
- [ ] MCP server só leitura para pesquisa/recomendação.
- [ ] Dashboard local da biblioteca; revisão de duplicatas; busca FTS.
- [ ] Backup/exportações de favoritos reorganizados, sem escrita em arquivos vivos do browser.
- [ ] Sync periódico opt-in, checkpoints, limites, retry.
- [ ] Benchmark com 5k entradas e teste Windows end-to-end.

## Requisitos de qualidade em toda release
- Testes automatizados e relato de falhas.
- Nenhum token em log/commit e nenhuma execução remota não solicitada.
- Idempotência, reversibilidade, dry-run verdadeiro.
- Diferenças explícitas entre recursos *observados*, *inferidos* e *recomendados*.
