# AssetTrack TI - Funcionalidades

> Sistema de Gerenciamento de Ativos de TI com interface web moderna e suporte a Docker.

---

## 🔐 Autenticação & Usuários

| Funcionalidade | Descrição |
|----------------|-----------|
| **Login Tradicional** | Autenticação com email/senha e JWT. |
| **Login via QR** | Autenticação rápida com Crachá Digital + PIN. |
| **Meu QR Code** | Cada usuário possui um QR Code único para identificação e login. |
| **Níveis de Acesso** | `ADMIN`, `GERENTE_TI`, `TECNICO`, `USUARIO`. |

---

## 📦 Gestão de Ativos (E-Patrimônio)

O sistema utiliza o conceito de **E-Patrimônio** para identificação única dos ativos.

| Funcionalidade | Descrição |
|----------------|-----------|
| **Inventário** | Listagem completa com filtros por status, setor e localização. |
| **E-Patrimônio** | Identificador principal único (ex: EP-0001). |
| **Número de Série** | Registro do Serial Number do fabricante para rastreabilidade. |
| **Scanner QR** | Leitura instantânea de etiquetas para abrir detalhes do ativo. |
| **Movimentações** | Histórico completo de quem usou o ativo e por onde ele passou. |
| **Baixa de Ativos** | Registro de saída definitiva do inventário. |

---

## 🎧 Service Desk (Help Desk)

Módulo integrado para suporte técnico aos usuários.

- **Abertura de Chamados:** Categorias, setores e níveis de prioridade.
- **Interações:** Histórico de mensagens entre técnico e usuário.
- **Status:** Acompanhamento em tempo real (Aberto, Em Atendimento, Resolvido).
- **QR de Chamado:** Cada ticket possui um QR único para acesso rápido.

---

## 🛠️ Manutenção

- **Solicitação de Reparo:** Usuários podem relatar defeitos em seus equipamentos.
- **Painel Técnico:** Gestão de filas de conserto e troca de peças.
- **Validação de Entrega:** Uso do QR Code do usuário para confirmar a devolução do item reparado.

---

## 🎨 Design System: Industrial Technical

- Interface limpa e objetiva.
- Bordas retas e sombras sólidas (Estilo Industrial).
- Tipografia técnica e otimizada para leitura de dados.
- Totalmente responsivo para uso em tablets e smartphones.

---

## 🔧 Stack Tecnológica

- **Backend:** FastAPI (Python 3.11).
- **Frontend:** Jinja2 + Tailwind CSS.
- **Banco de Dados:** PostgreSQL (Dockerizado).
- **Infra:** Docker & Docker Compose.
