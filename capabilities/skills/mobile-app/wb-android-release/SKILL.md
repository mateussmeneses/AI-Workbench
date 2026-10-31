---
name: wb-android-release
description: Preparar build Android e aceite em aparelhos
version: 1.0.0
---
# wb-android-release

**Papel sugerido:** `mobile-engineer`. Este arquivo é portátil e não depende desse agente existir.

## Acionamento
 Build APK/AAB, assinatura, permissões Android, leitor de câmera ou notificações.
 ## Procedimento
 1. Confira variante, versão, applicationId, targetSdk, assinaturas e segredos fora do repositório.
 2. Construa artefato reproduzível; registre comandos e hashes, sem incluir keystore no Git.
 3. Teste ao menos dois aparelhos com versões Android diferentes, permissões negadas/aceitas e background.
 4. Valide notificações, scanner, offline, atualização e dados persistidos.
 ## Saída
 Checklist de publicação fechada, evidências por dispositivo e bloqueadores.
