# 🚀 Melhorias e Atualizações no Módulo de Service Desk

Este documento consolida todas as melhorias visuais, funcionais e de infraestrutura implementadas no módulo de **Service Desk** da plataforma **AssetTrack TI**.

---

## 📋 1. Novas Funcionalidades e Melhorias

### 📸 A. Linha do Tempo (Timeline) com Upload de Imagens
* **Descrição:** Adição de suporte a upload de imagens de forma bidirecional (tanto na abertura do chamado quanto em cada interação/comentário).
* **Benefício:** Permite que usuários enviem capturas de tela (prints) de erros de software e que técnicos registrem fotos do hardware/peças como evidências físicas.
* **Componentes Afetados:**
  * [detail.html](file:///home/humberto/Aplicativos/Assettrackti/assettrack_ti/app/templates/service_desk/detail.html): Formulário de interações atualizado com suporte a `multipart/form-data` e exibição de fotos com molduras técnicas estilizadas.
  * [form.html](file:///home/humberto/Aplicativos/Assettrackti/assettrack_ti/app/templates/service_desk/form.html): Formulário de abertura com suporte a uploads.
  * [service_desk.py](file:///home/humberto/Aplicativos/Assettrackti/assettrack_ti/app/web/endpoints/service_desk.py): Endpoints POST de criação de chamado e comentários atualizados para processar e salvar imagens no diretório de uploads do servidor.

### 📊 B. Dashboard Gerencial Premium (ApexCharts)
* **Descrição:** Painel estatístico e analítico moderno, de visualização restrita para **Administradores** e **Gerentes**.
* **Gráficos Integrados:**
  1. **Status dos Chamados:** Gráfico de Rosca (Donut) interativo.
  2. **Chamados por Prioridade:** Gráfico de Barras Radial.
  3. **Volume de Solicitações por Usuário:** Gráfico de Colunas Neo-Brutalista.
* **Filtros Avançados:** Posicionados estrategicamente **logo abaixo dos gráficos e acima da lista de chamados**, oferecendo um fluxo de usabilidade fluido e otimizado para pesquisar por texto, status, categoria, prioridade e datas.

### 🔗 C. Códigos Estruturados & QR Code do Ticket
* **Descrição:** Substituição do ID numérico sequencial por um código profissional estruturado no formato `CH-2026-XXXX`.
* **Rastreabilidade Dinâmica:**
  * Cada chamado agora possui uma URL limpa (ex: `/servicos/chamado/CH-2026-0001`).
  * Geração dinâmica de um **QR Code único** exibido diretamente no topo do chamado, acima do código, permitindo que técnicos ou usuários escanear o chamado com a câmera do celular para acessá-lo instantaneamente via link mobile.

### ⏰ D. Alinhamento de Fuso Horário (UTC-3)
* **Descrição:** Correção dos horários de abertura e atualizações de chamados para obedecerem rigorosamente ao fuso horário brasileiro (`America/Sao_Paulo` ou UTC-3).
* **Solução:** Substituição de `datetime.now()` por `now_sp()` centralizado a nível de banco de dados e aplicação.

---

## 🐳 2. Infraestrutura: Persistência de Uploads no Docker

### 🔍 O Problema Diagnosticado
Anteriormente no ambiente Docker de desenvolvimento:
1. O `Dockerfile` de desenvolvimento não copiava a pasta `static` no build da imagem, e o `docker-compose.yml` não a montava como volume.
2. Com isso, o diretório `/code/static` não existia no startup do container, fazendo o FastAPI **pular completamente a inicialização e montagem do roteador `/static`**.
3. Qualquer arquivo enviado era salvo localmente dentro do container, mas retornava **Erro 404** ao tentar ser exibido, além de ser excluído toda vez que o container reiniciava.

### 🛠️ A Solução Arquitetural Aplicada
1. **Mapeamento de Volume:** Adicionado o mapeamento `- ./static:/code/static` no [docker-compose.yml](file:///home/humberto/Aplicativos/Assettrackti/assettrack_ti/docker-compose.yml). As fotos salvas agora são gravadas diretamente no disco do computador do host de forma permanente.
2. **Montagem Uncondicional:** Alterado [app/main.py](file:///home/humberto/Aplicativos/Assettrackti/assettrack_ti/app/main.py) para sempre criar a pasta no startup (`os.makedirs`) caso ela falte, e montá-la incondicionalmente no roteador do FastAPI.

---

## 🚀 3. Instruções de Deploy e Commit (Push Force)

Para subir todas as melhorias do seu ambiente de desenvolvimento para o repositório no **GitHub**, execute a sequência de comandos abaixo diretamente no terminal da sua máquina (onde as suas chaves SSH de autenticação com o GitHub estão ativas):

```bash
# 1. Configura sua identidade local no Git para este repositório
git config user.name "Humberto"
git config user.email "humberto@example.com"

# 2. Adiciona todos os arquivos novos e modificados para o commit
git add .

# 3. Cria um commit descritivo e organizado
git commit -m "feat: service desk advanced dashboard, timeline images, CH-2026 QR link codes, SP time zone corrections and persistent mounts"

# 4. Faz o push forçado (push force) enviando as modificações diretamente para o GitHub na branch ativa
git push origin $(git branch --show-current) --force
```

### ⚙️ Atualizando o Servidor/Docker Localmente
Após realizar o commit, para aplicar todas as mudanças de volume e código na sua máquina local ou em produção, basta rodar:

```bash
./update_docker.sh
```

---
*Documentação criada em 17 de Maio de 2026 // Equipe Antigravity Kit.*
