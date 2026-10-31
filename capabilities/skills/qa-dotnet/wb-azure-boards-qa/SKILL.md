---
name: wb-azure-boards-qa
description: Rastrear critérios e evidências no Azure Boards
version: 1.0.0
---
# wb-azure-boards-qa

**Papel sugerido:** `qa-strategist`. Este arquivo é portátil e não depende desse agente existir.

## Acionamento
 Homologação associada a work item, feature, task, bug ou sprint no Azure DevOps.
 ## Procedimento
 1. Leia o item e links relacionados via ferramenta autorizada; extraia critérios e estados oficiais.
 2. Construa matriz item → regra → teste → evidência, separando bloqueios.
 3. Verifique workflow de aprovação, sprint, dependências e regressões relevantes.
 4. Proponha atualização no work item; não altere status automaticamente sem autorização.
 ## Saída
 Relatório de homologação e itens que exigem esclarecimento.
