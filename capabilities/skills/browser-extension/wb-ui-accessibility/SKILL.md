---
name: wb-ui-accessibility
description: Auditar legibilidade e acessibilidade de UI
version: 1.0.0
---
# wb-ui-accessibility

**Papel sugerido:** `browser-engineer`. Este arquivo é portátil e não depende desse agente existir.

## Acionamento
 Texto invisível, contraste baixo, layout escuro, elementos sobrepostos ou navegação difícil.
 ## Procedimento
 1. Verifique contraste, estados hover/focus/disabled, tipografia, overflow e tamanhos de alvo.
 2. Teste zoom 125–200%, light/dark, teclado e responsividade sem seleção de texto como workaround.
 3. Inspecione CSS computado e tokens; corrija na origem, não com exceções por componente.
 4. Colete comparativos antes/depois e smoke test visual.
 ## Saída
 Achados com seletor, causa CSS e validação por viewport/tema.
