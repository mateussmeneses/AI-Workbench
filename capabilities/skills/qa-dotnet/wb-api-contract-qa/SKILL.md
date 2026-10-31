---
name: wb-api-contract-qa
description: Testar contratos HTTP e persistência de APIs
version: 1.0.0
---
# wb-api-contract-qa

**Papel sugerido:** `qa-strategist`. Este arquivo é portátil e não depende desse agente existir.

## Acionamento
 Mudança em API, DTO, status HTTP, banco, XML/JSON ou regras de validação.
 ## Procedimento
 1. Mapeie request, response, esquema, autenticação, idempotência, transações e efeitos no banco.
 2. Compare antes/depois incluindo `null`, defaults, tipos, campos removidos e validação.
 3. Teste autorização, paginação, filtros, ordenação, bordas, timeout e erros.
 4. Colete evidência de API, logs e queries somente de leitura, exceto mudança aprovada.
 ## Saída
 Matriz de contrato e persistência, regressões e scripts de verificação.
