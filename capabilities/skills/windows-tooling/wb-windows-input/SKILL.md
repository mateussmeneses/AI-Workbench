---
name: wb-windows-input
description: Depurar controles e dispositivos Windows
version: 1.0.0
---
# wb-windows-input

**Papel sugerido:** `windows-engineer`. Este arquivo é portátil e não depende desse agente existir.

## Acionamento
 Input USB/Bluetooth, controle de jogo, XInput/RawInput, serviço Windows ou portabilidade desktop.
 ## Procedimento
 1. Mapeie dispositivos e versões de driver; colete logs sem alterar estado global.
 2. Reproduza com controle USB e sem fio; diferencie camada de HID, emulação e aplicação.
 3. Meça latência, reconexão, eventos duplicados, foco da janela, suspensão e hot-plug.
 4. Verifique empacotamento, privilégios, persistência e rollback de mudanças de serviço.
 ## Saída
 Matriz de hardware/driver, diagnóstico, teste e riscos.
