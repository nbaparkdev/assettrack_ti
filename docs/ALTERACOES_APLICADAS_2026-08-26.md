# Alterações Aplicadas — AssetTrack TI

**Data:** 26/08/2026  
**Commit principal:** `ccc7d33` — `feat: sincroniza rede e atualiza recursos do aplicativo`  
**Branch publicada:** `main`  
**Repositório:** https://github.com/nbaparkdev/assettrack_ti.git

## 1. Kanban

- Corrigido o modo fullscreen para manter comandos, menus e modais totalmente funcionais.
- O elemento de fullscreen foi reposicionado para não bloquear interações da aplicação.
- O texto **“Criado por”** no cabeçalho do quadro foi ampliado de 10px para 14px.
- Preservadas as funcionalidades de criação, edição e movimentação de cartões.

## 2. Alertas e chamados

- Alertas relacionados a chamados agora abrem diretamente o chamado correspondente.
- Adicionada a referência do chamado nos dados dos alertas.
- Corrigida a navegação do painel de alertas para a Central de Suporte.
- O alerta emergencial continua abrindo o modal emergencial já existente.
- O som de alerta passou a utilizar o arquivo `notificacao_alerta.mp3`.

## 3. Sala de Monitoramento

- Criada a página `/monitoramento` para uso em TV ou tela de monitoramento.
- Interface moderna em modo escuro, com logo centralizada no topo.
- Indicadores de chamados abertos, prioridades altas, manutenções e alertas ativos.
- Fila de atendimento com título, protocolo, solicitante, prioridade, status e responsável.
- Status do atendimento e técnico/responsável atribuído exibidos em tempo real.
- Central de alertas com atualização automática.
- Inclusão das solicitações de ativos pendentes e aprovadas aguardando entrega.
- Atualização automática dos dados a cada 5 segundos.
- Integração com eventos SSE para atualização em tempo real.
- Som e notificação visual quando surge ou é alterado um chamado, alerta, manutenção ou solicitação.
- Botão para entrar e sair do fullscreen.
- Acesso restrito a administradores, gerentes e técnicos autorizados.

## 4. Notificações Android

- Adicionado o plugin de notificações locais do Capacitor.
- Criado o canal Android `assettrack-alertas` com alta prioridade.
- Configurados som, vibração, luzes e notificações visuais.
- Incluída solicitação de permissão `POST_NOTIFICATIONS` para versões recentes do Android.
- Adicionado o áudio de alerta aos recursos web e Android.
- Notificações disparadas para alertas emergenciais e novos eventos do monitoramento.
- Mantido o fluxo de reprodução sonora dentro da aplicação.

> Observação: notificações push quando o aplicativo estiver completamente encerrado exigem integração futura com Firebase Cloud Messaging (FCM).

## 5. Ativos e inventário

- Corrigida a busca de ativos vinculados ao usuário quando o status está registrado como `Em uso` ou `Uso`.
- Corrigido o vínculo de equipamentos em posse do usuário.
- Após editar um ativo, a tabela recebe imediatamente o retorno atualizado da API.
- Adicionada nova consulta ao servidor após o salvamento para atualizar nomes de local, armazenamento, setor e responsável.
- Quando o ativo está `Em Uso`, o campo **Em Posse De** é sincronizado automaticamente com o usuário cadastrado.
- A interface prioriza o usuário atualmente vinculado ao ativo, evitando exibição de texto antigo.
- Histórico de alertas antigos é enriquecido com os ativos atuais do usuário quando necessário.

## 6. Logos e identidade visual

- Logo clara AssetTrack adicionada ao portal.
- Logo adicionada à tela de login.
- Logo de monitoramento adicionada à Sala de Monitoramento.
- Logo de monitoramento ajustada para melhor visibilidade no topo da TV.
- Arquivos adicionados:
  - `frontend/public/logo-assettrack-claro.svg`
  - `frontend/public/logo-assettrack-monitoramento.png`

## 7. Manual do sistema

- Criada a página `/manual` com apresentação visual moderna.
- Manual organizado por perfil de acesso.
- Conteúdo separado para administrador, gerentes, técnicos, compras, RH e usuário comum.
- Adicionadas ilustrações, atalhos e orientações dos principais módulos.
- Ícone de ajuda do cabeçalho direciona para o manual.
- Manual incluído no menu lateral.
- README e documentações funcionais atualizados.

## 8. Rede e acesso por outros dispositivos

- Rede Wi-Fi atual identificada: `172.30.6.127`.
- Gateway atual: `172.30.6.1`.
- Portal web disponível em:
  - `http://172.30.6.127:8000`
- API disponível em:
  - `http://172.30.6.127:8080`
- Portas 8000 e 8080 publicadas em todas as interfaces do servidor.
- O APK foi atualizado para usar o endereço atual da API.
- Dispositivos precisam estar conectados à mesma rede Wi-Fi.

> O endereço foi obtido via DHCP e pode mudar. Para uso permanente, recomenda-se reservar o IP no roteador ou configurar um endereço fixo.

## 9. APK Android

- APK recompilado com as funcionalidades mais recentes.
- Build de release assinado concluído.
- Versão publicada: `2026.08.26.1730`.
- Código da versão: `1787765459`.
- Tamanho: aproximadamente 4,7 MB.
- Download pelo servidor:
  - `http://172.30.6.127:8080/api/v1/app/download`
- Arquivo publicado no servidor:
  - `backend/uploads/AssetTrack-TI-v2026.08.26.1730.apk`
- Manifest de versão atualizado em `backend/uploads/mobile-release.json`.
- A pasta de uploads permanece fora do versionamento Git; o código-fonte e os recursos necessários estão no repositório.

## 10. Validações realizadas

- Build do frontend concluído com sucesso.
- Testes do backend para handlers e repositórios concluídos com sucesso.
- Build Android de release concluído com sucesso usando Java 21.
- Portal web respondendo na rede local.
- API respondendo com HTTP 200.
- Containers web, API, banco e Redis em execução.
- APK registrada no endpoint de versão e disponível para download.

## 11. Publicação no GitHub

- Todas as alterações foram adicionadas ao Git.
- Commit criado: `ccc7d33`.
- Push realizado com sucesso para `origin/main`.
- O diretório de trabalho foi conferido após o push e ficou limpo.

## Arquivos e áreas principais alterados

- `backend/internal/handler/asset.go`
- `backend/internal/handler/alerts_handler.go`
- `backend/internal/handler/dashboard_handler.go`
- `backend/internal/repository/asset_repo.go`
- `frontend/src/pages/AssetsPage.tsx`
- `frontend/src/pages/KanbanPage.tsx`
- `frontend/src/pages/MonitoramentoPage.tsx`
- `frontend/src/pages/ManualPage.tsx`
- `frontend/src/components/emergency/EmergencyGlobalHandler.tsx`
- `frontend/src/utils/androidNotifications.ts`
- `frontend/src/utils/audio.ts`
- `frontend/src/api/client.ts`
- `frontend/android/app/src/main/AndroidManifest.xml`
- `frontend/public/logo-assettrack-claro.svg`
- `frontend/public/logo-assettrack-monitoramento.png`
- `frontend/public/notificacao_alerta.mp3`
- `README.md` e demais documentações em `docs/`
