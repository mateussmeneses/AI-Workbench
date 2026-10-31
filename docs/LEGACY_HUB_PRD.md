# PRD — AI Workbench Hub

## Problema
Ferramentas e guias acumulam-se em favoritos do navegador, stars do GitHub, múltiplos agentes e skills. Cada projeto exige redescobrir o que é útil, com risco de perder contexto, ativar ferramentas irrelevantes e executar scripts não auditados.

## Solução
Um **catálogo pessoal, local-first e reutilizável** de links e capacidades, com classificação multi-rótulo, curadoria, recomendações por repositório e adaptadores opcionais para Codex/Hermes/OpenClaude.

## Usuário-alvo
Desenvolvedor/QA com projetos paralelos .NET/QA, game porting/Vulkan, extensões MV3, Android, IA e Windows.

## Jornada desejada
1. Importar bookmarks dos perfis locais e as stars autenticadas via `gh`, em read-only.
2. Deduplicar sem apagar histórico ou origem; classificar e revisar os incertos.
3. Abrir repositório novo, executar `aiwh attach --project .` ou launcher integrado.
4. Receber poucas referências e skills relevantes, cada qual com motivo de seleção.
5. Alternar Codex, Hermes, OpenClaude mantendo links/skills relevantes, sem carregar todos os MCPs.
6. Atualizar biblioteca e reclassificar recursos com diff e auditoria.

## Prioridade P0
- Chromium JSON multi-profile, browser HTML export, `gh api --paginate`, ingestão incremental, origem.
- Catálogo local privado, canonicalização de URL, duplicados e revisão.
- Taxonomia configurável e classificação multi-rótulo.
- Detecção por repositório, preview e acoplamento local idempotente.
- Testes e documentação Windows.

## P1
- SQLite FTS5, ranking por tarefa e metadados GitHub, agentes/skills recomendados.
- Adapter Codex (AGENTS/skills) e primeiros adaptadores Hermes/OpenClaude.
- UI local de revisão, bookmarks export organizado, nunca modificar perfil vivo.

## P2
- MCP server read-only, sync incremental agendada opt-in, embeddings locais, avaliação de reputação/proveniência e ranking com feedback.

## Requisitos não funcionais
- Leitura somente na fonte, sem execução de conteúdo importado.
- Não publicar favoritos e credenciais. Índice canônico fora de Git.
- Sem dependência obrigatória de API paga.
- Suportar 5 mil recursos com testes de desempenho.
- Operações idempotentes, dry-run e logs redigidos.
