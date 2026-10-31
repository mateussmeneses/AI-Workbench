---
name: wb-bdd-reqnroll
description: Especificar BDD com NUnit e Reqnroll
version: 1.0.0
---
# wb-bdd-reqnroll

**Papel sugerido:** `qa-strategist`. Este arquivo é portátil e não depende desse agente existir.

## Acionamento
 Casos BDD, automação .NET, step definitions e parametrização de features.
 ## Procedimento
 1. Localize `.feature`, step definitions, pages, fixtures e convenções já usadas.
 2. Escreva Given/When/Then orientado a regra, não a cliques; reutilize steps existentes.
 3. Mantenha cenários independentes, dados explícitos e asserts do comportamento (incluindo toasts e permissões).
 4. Execute `dotnet test` com filtro apropriado; registre falha ambiental separadamente da falha funcional.
 ## Saída
 Cenários novos/alterados, lacunas de cobertura e comandos/resultados.
