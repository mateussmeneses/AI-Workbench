---
name: wb-extension-mv3
description: Revisar arquitetura e permissões de extensões MV3
version: 1.0.0
---
# wb-extension-mv3

**Papel sugerido:** `browser-engineer`. Este arquivo é portátil e não depende desse agente existir.

## Acionamento
 Extensão Chrome/Edge, manifest V3, service worker, content scripts e injeções.
 ## Procedimento
 1. Inspecione `manifest.json`, escopo de host permissions, service worker e content scripts.
 2. Identifique mensagens, ciclo de vida, persistência, versão de API e CSP.
 3. Teste em DOM mutável, navegação SPA, aba recarregada, injeção duplicada e permissões negadas.
 4. Valide acessibilidade, contraste, isolamento e degradação graciosa.
 ## Saída
 Riscos de permissão/estado, testes manuais/automatizados e recomendações mínimas.
