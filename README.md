
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

Módulo integrado para gestão de chamados de suporte técnico.

| Recurso | Descrição |
| :--- | :--- |
| **Abertura de Chamados** | Relato de problemas por categorias e setores |
| **Dashboard e Estatísticas** | Painel em tempo real (Abertos, Em Atendimento, Resolvidos) |
| **Gestão de Interações** | Histórico de comunicação entre técnicos e usuários |
| **Integração QR Code** | QR Code único por chamado para acompanhamento ágil |

## 📱 Sistema de QR Code

Funcionalidades de identificação e login rápido.

| Recurso | Descrição |
| :--- | :--- |
| **Crachá Digital** | QR Code único por usuário |
| **Login via QR** | Login rápido via QR + PIN |
| **Histórico de Ativos** | Scanner revela histórico completo (E-Patrimonio) |

> 📸 **Nota sobre Scanner via Rede Local (HTTP):**
> Navegadores bloqueiam a câmera em conexões HTTP. Para liberar em sua rede local:
> 1. No Chrome/Edge, acesse: `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
> 2. Em "Insecure origins treated as secure", adicione o endereço: `http://SEU_IP:8000`
> 3. Mude para **Enabled** e reinicie o navegador.

---

## 🛠️ Segurança e Auditoria

- 🔒 **Rate Limiting**: Proteção contra força bruta nos logins.
- ⏰ **Expiração**: Tokens QR configuráveis.
- 🔐 **PIN**: Obrigatório para ações via QR Code.
- 📝 **Logs**: Registro completo de movimentações e logins.
