# MCPs: catálogo, não instalador

A ligação MCP varia por cliente e credencial. Este kit **não ativa MCPs** e não escreve segredos.

| MCP | Ativar quando | Alternativa leve |
|---|---|---|
| GitHub | Issues, PRs, branches e revisões remotas | `gh` CLI |
| Azure DevOps | Work items, boards, builds | interface web / REST autorizada |
| Playwright | Interação com browser real | testes locais Playwright/Selenium |
| Chrome DevTools | network, traces, console, performance | DevTools manual |
| Context7 | Docs de biblioteca/versão que mudam | docs oficiais |

## Hermes
Documentação: https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp
Catálogo: `hermes mcp catalog`. Gerencie por `hermes mcp` ou `mcp_servers` no `~/.hermes/config.yaml`. Use `enabled: false` em servidores não necessários; `lazy: true` quando suportado. Após mudanças: `/reload-mcp`.

## Fontes oficiais
- GitHub MCP: https://github.com/github/github-mcp-server
- Azure DevOps: https://github.com/microsoft/azure-devops-mcp (servidor remoto recomendado)
- Playwright: https://github.com/microsoft/playwright-mcp
- Chrome DevTools: https://github.com/ChromeDevTools/chrome-devtools-mcp
- Context7: https://github.com/upstash/context7

Trate credenciais como segredos; prefira login/OAuth e variáveis de ambiente. Nunca escreva PAT ou chave no AGENTS.md, histórico do Git ou arquivos de skill.
