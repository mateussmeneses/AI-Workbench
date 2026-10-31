---
name: wb-board-snapshots
description: Validar contagem e snapshots de quadros Kanban
version: 1.0.0
---
# wb-board-snapshots

**Papel sugerido:** `browser-engineer`. Este arquivo é portátil e não depende desse agente existir.

## Acionamento
 WIP board, counters, snapshot diário, cartões invisíveis e progresso de sprint.
 ## Procedimento
 1. Identifique board, colunas, estados e regras de negócio; diferencie total de cartões de contador exibido.
 2. Conte cartões no DOM inclusive colunas sem badge/contador e regiões sob overlays quando acessíveis.
 3. Compare resultado do snapshot com contagem visível sob filtros e agrupamentos.
 4. Teste múltiplos boards isoladamente, resets, persistência, datas e sincronização de dados.
 ## Saída
 Matriz board × coluna × contagem UI × snapshot × divergência, com evidências.
