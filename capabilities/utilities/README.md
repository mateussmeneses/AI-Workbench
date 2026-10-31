# Utilitários por contexto

Ferramentas aqui são **recomendações condicionais**, não instaladas automaticamente. Instale apenas quando requisitadas.

| Núcleo | `git`, `gh`, `rg` (ripgrep), `fd`, `jq`, `python`, `node`, PowerShell 7 |
|---|---|
| QA .NET | `.NET SDK`, `dotnet test`, NUnit, Reqnroll, Selenium/Appium, logs, SQL de leitura |
| Porting | RenderDoc, Vulkan SDK/Validation Layers, captura de frametime, FFmpeg, ferramentas RE conforme arquivo/build |
| Extensões | Chrome/Edge DevTools, Node.js, testes DOM, Playwright, lint |
| Mobile | Android SDK/ADB, Gradle, emulador/aparelhos físicos, testes de permissão |
| Windows | PowerShell, Event Viewer, Windows SDK, ferramentas HID/controle conforme o problema |

## Política operacional
1. Reaproveite CLI existente em vez de adicionar MCP redundante.
2. Fixe versões usadas em reprodução e gere `logs/`/`artifacts/` ignorados por Git.
3. Não instale/desative serviços, drivers ou hooks globalmente como efeito colateral de setup.
4. Reporte comandos e resultados; nunca invente medições.
