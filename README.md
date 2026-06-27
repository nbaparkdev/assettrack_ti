
# README - AssetTrack TI

Sistema de Controle de Ativos de TI completo em Python (FastAPI).

[Consulte os Requisitos do Sistema aqui](./REQUIREMENTS.md) | [Política de Segurança](./SECURITY.md) | [Licença](./LICENSE)

## Estrutura
- **app/models**: Modelos do Banco de Dados (SQLAlchemy)
- **app/schemas**: Schemas de Validação (Pydantic)
- **app/api**: Endpoints da API REST
- **app/services**: Serviços de QR Code e Email

## 🚀 Como Rodar (Recomendado: Docker)

Certifique-se de ter Docker e Docker Compose instalados.

### 1. Inicialização Rápida (Automação)
O projeto inclui um script que configura o ambiente, sobe os containers e inicializa o usuário administrador automaticamente:

```bash
chmod +x init_docker.sh
./init_docker.sh
```

### ⚙️ Utilitários de Gestão
Para facilitar a manutenção, você pode usar os seguintes scripts:

*   **Parar aplicação:**
    ```bash
    ./stop_docker.sh
    ```
*   **Atualizar aplicação (Git Pull + Rebuild):**
    ```bash
    ./update_docker.sh
    ```

### 2. Inicialização Manual
Caso prefira rodar os comandos passo a passo:

1.  **Configurar ambiente:**
    ```bash
    cp .env.example .env
    ```
2.  **Subir os containers:**
    ```bash
    docker-compose up -d --build
    ```
3.  **Acesse o sistema:**
    - App: [http://localhost:8000](http://localhost:8000)
    - Documentação (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔑 Usuários Padrão

Credenciais sugeridas para teste:

| Perfil | Email | Senha | Acesso |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@example.com` | `admin` | Total (Configurações, Usuários, Ativos) |
| **Técnico** | `tecnico@example.com` | `123` | Operacional (Manutenções e Devoluções) |

### Gerenciar usuários via terminal (Docker)
Se precisar criar ou ativar usuários manualmente:

```bash
# Criar/Ativar Admin
docker-compose exec web python create_admin.py
docker-compose exec web python activate_user_admin.py

# Criar Técnico
docker-compose exec web python create_technician.py
```

---

## 🏢 Gestão de Fornecedores e Notas Fiscais

O sistema possui um módulo completo para controle e relacionamento de Fornecedores e Notas Fiscais de Ativos.

| Recurso | Descrição |
| :--- | :--- |
| **Cadastro de Fornecedores** | Registro de dados (Razão Social, CNPJ, Contato, Endereço e Tipo) |
| **Integração XML** | Upload de Notas Fiscais em formato `.xml` |
| **Vínculo com Ativos** | Seleção de fornecedor no cadastro de novos ativos |
| **Rastreabilidade** | Vínculo automático de Nota Fiscal ao fornecedor |
| **Upload de Imagens** | Foto/comprovante do equipamento no servidor |

## 🎧 Service Desk (Help Desk)

Módulo integrado e moderno para gestão de chamados de suporte técnico.

| Recurso | Descrição |
| :--- | :--- |
| **Abertura de Chamados** | Relato de problemas por categorias e setores com suporte a upload de imagens de identificação. |
| **Painel de Gráficos (ApexCharts)** | Dashboard analítico premium (distribuição por status, prioridades, categorias e top solicitantes) restrito a Administradores e Gerentes. |
| **Filtros Avançados de Busca** | Filtros posicionados estrategicamente abaixo dos gráficos para pesquisa refinada por texto, status, categoria, prioridade e intervalo de datas. |
| **Timeline Interativa** | Histórico cronológico completo de interações com suporte a fotos tanto para técnicos quanto para solicitantes (reforço visual dos serviços). |
| **Formato Profissional de Código** | Chamados gerados em formato estruturado (Ex: `CH-2026-0001`), com links permanentes amigáveis para organização. |
| **QR Code do Chamado** | Código QR gerado automaticamente e impresso acima do código do chamado para acesso e acompanhamento mobile rápido. |
| **Fuso Horário Local Preciso** | Registro de abertura e interações ajustado perfeitamente ao fuso horário `America/Sao_Paulo` (UTC-3). |

## 📱 Sistema de QR Code

Funcionalidades de identificação, login rápido e acompanhamento ágil.

| Recurso | Descrição |
| :--- | :--- |
| **Crachá Digital** | QR Code único por usuário. |
| **Login via QR** | Login rápido via QR + PIN. |
| **Acompanhamento de Chamados** | QR Code impresso nos chamados vinculando ao link direto de atendimento mobile (`/servicos/chamado/CH-2026-0001`). |
| **Histórico de Ativos** | Scanner revela histórico completo de movimentação (E-Patrimonio). |

> 📸 **Nota sobre Scanner via Rede Local (HTTP):**
> Navegadores bloqueiam a câmera em conexões HTTP. Para liberar em sua rede local:
> 1. No Chrome/Edge, acesse: `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
> 2. Em "Insecure origins treated as secure", adicione o endereço: `http://SEU_IP:8000`
> 3. Mude para **Enabled** e reinicie o navegador.

---

## 🔧 Manutenção Preventiva (CMMS/EAM)

Módulo completo para gestão de manutenção preventiva, corretiva e periódica integrado ao AssetTrack TI.

| Recurso | Descrição |
| :--- | :--- |
| **Planos de Manutenção** | Registro de planos periódicos, definindo tipo (Preventiva/Preditiva/Inspeção/Calibração), periodicidade, criticidade e prioridade. |
| **Ordens de Serviço** | Criação manual ou automática de ordens de manutenção (OS), com histórico de execução e acompanhamento de status em tempo real. |
| **Checklists de Manutenção** | Cadastro de itens de verificação obrigatórios para cada tipo de manutenção. |
| **Histórico Completo** | Auditoria completa de todas as ações, incluindo execução de checklists, fotos e materiais utilizados. |
| **Dashboard Analítico** | Painel com métricas (manutenções vencidas/hoje/semana), gráficos (Preventiva vs Corretiva, status das ordens, ordens por técnico) e próximas manutenções agendadas. |
| **Geração Automática de Códigos** | Planos no formato `PLAN-ANO-NÚMERO` e ordens no formato `OS-ANO-NÚMERO`. |
| **Integração com Ativos** | Vinculação de ativos aos planos e ordens, com histórico completo. |
| **Segurança por Permissões** | Acesso controlado por perfis: Admin, Gerente, Técnico, Usuário. |

## 🛠️ Segurança e Auditoria

- 🔒 **Rate Limiting**: Proteção contra força bruta nos logins.
- ⏰ **Expiração**: Tokens QR configuráveis.
- 🔐 **PIN**: Obrigatório para ações via QR Code.
- 📝 **Logs**: Registro completo de movimentações e logins.
