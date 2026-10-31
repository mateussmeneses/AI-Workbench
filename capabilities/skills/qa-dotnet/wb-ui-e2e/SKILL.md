---
name: wb-ui-e2e
description: Automatizar interface com locators estáveis
version: 1.0.0
---
# wb-ui-e2e

**Papel sugerido:** `qa-strategist`. Este arquivo é portátil e não depende desse agente existir.

## Acionamento
 Testes Selenium, Appium, Playwright ou falhas intermitentes de interface.
 ## Procedimento
 1. Escolha locator estável (`data-testid` quando disponível), evite indexação e esperas fixas.
 2. Sincronize por condição observável; mantenha teste isolado, sem estado implícito.
 3. Registre console, rede, screenshots, tempos e estado real apenas quando pertinente.
 4. Execute teste repetido no pipeline/local e diferencie flake de regressão.
 ## Saída
 Teste reproduzível, qualidade de seletores e evidência de estabilidade.
