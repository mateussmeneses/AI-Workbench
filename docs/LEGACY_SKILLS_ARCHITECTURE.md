# Método de separação

## Seis camadas
1. **Core**: skills transversais e convenções mínimas (`AGENTS.md`).
2. **Perfil**: seleção declarativa de skills e papéis por tipo de projeto.
3. **Skill**: procedimento com trigger, passos, verificações e resultado esperado (`SKILL.md`).
4. **Agent role**: papel operacional; arquivo de instruções independente do runtime, não um subagente nativo automaticamente.
5. **MCP**: servidor de dados/ações externas; ativação restrita, com credenciais fora do Git.
6. **Utilities**: executáveis locais para medir, compilar e testar; preferir ao MCP quando suficientes.

## Política de ciclo de vida
- Resolvedor: ler objetivo -> core -> um perfil -> 1–2 skills -> papel -> MCP apenas se necessário.
- Conversa: REPRO/BASELINE -> PLANO -> IMPLEMENTAÇÃO -> TESTE -> REVIEW -> PR/RELEASE.
- Uma skill nova nasce de repetição **observada**, não de uma única solução isolada.
- Evitar regras contraditórias: instruções de projeto prevalecem no projeto; registrar exceções em `AGENTS.md`.
- Subagentes devem trazer evidências independentes; não peça quatro agentes para fazer a mesma leitura de arquivo.
- Uma única fonte de verdade para as skills globais (`~/.agents/skills`); especializados ficam no próprio repo.
- A cada trimestre: auditar duplicidade, desuso, tempo de execução, rate limit e testes falhando.

## Interoperabilidade
- Hermes: `~/.hermes/config.yaml` `skills.external_dirs: [~/.agents/skills]` para global; `.agents/skills/` no projeto; `hermes skills trust` no repo.
- OpenClaude: `~/.agents/skills/` global; `.openclaude/skills/` no projeto; validar com `openclaude skills validate`.
- Codex: `.agents/skills/` compartilhada e `AGENTS.md` com regras por projeto.
- Os arquivos em `agents/` são **templates de papéis**. Para execução como subagente nativo, criar adaptador no runtime selecionado; este kit não simula suporte inexistente.

## Segurança e governança
- Não gravar tokens, cookies, PATs, certificados nem chaves; nunca imprimir segredos em logs.
- O instalador não modifica `~/.hermes/config.yaml`, não instala MCP e não faz merge.
- Instalação idempotente; colisões existentes são ignoradas, salvo `-Force` explícito.
- Ajustes na produção e operações destrutivas exigem autorização e plano de rollback.
