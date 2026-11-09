# Utilitários por contexto

Ferramentas aqui são **recomendações condicionais**, não instaladas automaticamente. Instale apenas quando requisitadas.

| Núcleo | `git`, `gh`, `rg` (ripgrep), `fd`, `jq`, `python`, `node`, PowerShell 7 |
|---|---|
| QA .NET | `.NET SDK`, `dotnet test`, NUnit, Reqnroll, Selenium/Appium, logs, SQL de leitura |
| Porting | RenderDoc, Vulkan SDK/Validation Layers, captura de frametime, FFmpeg, ferramentas RE conforme arquivo/build |
| Extensões | Chrome/Edge DevTools, Node.js, testes DOM, Playwright, lint |
| Mobile | Android SDK/ADB, Gradle, emulador/aparelhos físicos, testes de permissão |
| Windows | PowerShell, Event Viewer, Windows SDK, ferramentas HID/controle conforme o problema |
| Engenharia reversa | [Ghidra](https://github.com/NationalSecurityAgency/ghidra), [ImHex](https://github.com/WerWolv/ImHex), [x64dbg](https://github.com/x64dbg/x64dbg), [Frida](https://github.com/frida/frida), [Kaitai Struct](https://github.com/kaitai-io/kaitai_struct), [binwalk](https://github.com/ReFirmLabs/binwalk) |
| Managed/Android | [ILSpy](https://github.com/icsharpcode/ILSpy), [jadx](https://github.com/skylot/jadx), [Apktool](https://github.com/iBotPeaches/Apktool), [apk.sh](https://github.com/ax/apk.sh), [APKEditor](https://github.com/REAndroid/APKEditor) |
| Web/Electron/APIs | [webcrack](https://github.com/j4k0xb/webcrack), [asar](https://github.com/electron/asar), [mitmproxy](https://github.com/mitmproxy/mitmproxy), [mitmproxy2swagger](https://github.com/alufers/mitmproxy2swagger), [Scrapling](https://github.com/D4Vinci/Scrapling) |
| Shader/PC gaming | [SCSKiller](https://github.com/BlueHeisenberg/SCSKiller) (pré-compilação de cache de shaders), [Magpie](https://github.com/Blinue/Magpie) (upscaling de janela) |

## Política operacional
1. Reaproveite CLI existente em vez de adicionar MCP redundante.
2. Fixe versões usadas em reprodução e gere `logs/`/`artifacts/` ignorados por Git.
3. Não instale/desative serviços, drivers ou hooks globalmente como efeito colateral de setup.
4. Reporte comandos e resultados; nunca invente medições.
