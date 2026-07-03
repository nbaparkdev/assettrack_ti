# TODO - Manutenção Preventiva (CMMS/EAM)

## ✅ Já Implementado
- [x] Modelos SQLAlchemy para todo o módulo
- [x] Schemas Pydantic para validação
- [x] CRUD operations para todos os modelos
- [x] API REST endpoints completos
- [x] Web endpoints básicos (listagem, criação, detalhes) para planos e ordens
- [x] Templates HTML seguindo o padrão do projeto
- [x] Integração com o menu de navegação
- [x] Dashboard básico com métricas
- [x] Geração automática de códigos para planos (`PLAN-ANO-NÚMERO`) e ordens (`OS-ANO-NÚMERO`)
- [x] Integração com o sistema de permissões

---

## 🔄 Em Desenvolvimento

### 🟢 Alta Prioridade
- [x] **Implementar auto-geração de ordens de serviço a partir de planos**:
  - [x] Criar job/serviço periódico que verifica próximas execuções
  - [x] Gerar ordens automaticamente quando a data chegar
- [x] **Implementar transições de status das ordens**:
  - [x] Iniciar ordem (`Em Andamento`)
  - [x] Pausar ordem (com cálculo de tempo acumulado)
  - [x] Concluir ordem (com solução, custo, atualização de próxima execução do plano)
  - [x] Cancelar ordem (somente Admin/Gerente)
  - [x] Registro automático de histórico em cada transição
- [x] **Implementar gerenciamento de checklists**:
  - [x] Adicionar checklists aos planos de manutenção
  - [x] Adicionar/remover itens de checklist (com flag obrigatório)
  - [x] Visualizar checklists nas ordens
  - [x] Marcar itens de checklist como concluídos durante a execução

### 🟡 Média Prioridade
- [x] **Implementar visualização de Calendário**:
  - [x] Criar página de calendário
  - [x] Exibir ordens e próximas manutenções no calendário
- [x] **Implementar gerenciamento de assets em planos**:
  - [x] Vincular múltiplos assets a um plano
  - [x] Editar/remover assets vinculados
- [x] **Implementar edição e exclusão de planos e ordens**:
  - [x] Endpoints para editar planos
  - [x] Endpoints para editar ordens
  - [x] Endpoints para excluir planos
  - [x] Endpoints para excluir ordens
- [x] **Implementar tracking de materiais**:
  - [x] Adicionar materiais a uma ordem
  - [x] Editar/remover materiais
  - [x] Calcular custo total da manutenção
- [x] **Implementar upload de fotos**:
  - [x] Upload de fotos para ordens
  - [x] Upload de fotos para execuções/checklists
  - [x] Visualizar galeria de fotos na ordem
- [x] **Implementar histórico completo**:
  - [x] Registrar todas as mudanças de status com MaintenanceHistory
  - [x] Visualizar timeline na página de detalhes da ordem
  - [x] Página de histórico completo com timeline visual
- [x] **Implementar relatórios**:
  - [x] Página de relatórios
  - [x] Relatório de manutenções concluídas no período
  - [x] Relatório de custos
  - [x] Relatório de desempenho dos técnicos
- [x] **Integrar QR Code às ordens**:
  - [x] Gerar QR Code para cada ordem
  - [x] Exibir QR Code na página de detalhes
  - [x] Permitir acesso rápido via QR

### 🟢 Baixa Prioridade
- [x] **Melhorar o dashboard**:
  - [x] Adicionar mais gráficos
  - [x] Adicionar filtros de período
  - [x] Adicionar métricas adicionais
- [x] **Implementar sistema de notificações**:
  - [x] Notificar técnicos sobre novas ordens
  - [x] Notificar sobre manutenções vencidas
  - [x] Notificar quando uma ordem é concluída
- [x] **Melhorar a UI/UX**:
  - [x] Adicionar feedback visual em formulários
  - [x] Melhorar a responsividade
  - [x] Adicionar animações

---

## 📂 Arquivos Importantes
- `app/models/preventive_maintenance.py`: Modelos do banco de dados
- `app/schemas/preventive_maintenance.py`: Schemas Pydantic
- `app/crud/preventive_maintenance.py`: Operações CRUD
- `app/api/v1/endpoints/preventive_maintenance.py`: API REST
- `app/web/endpoints/preventive_maintenance.py`: Endpoints Web
- `app/templates/preventive_maintenance/`: Templates HTML

---

## 🚀 Como Executar
```bash
# Ambiente local (sem Docker)
bash start_local.sh

# Acesse o sistema
# App: http://localhost:8000
# Swagger: http://localhost:8000/docs
```

---

## 🐛 Bugfixes & Ajustes Recentes (Jul/2026)
- [x] **Correção de Escopo Jinja2**: Corrigido bug de renderização no template `order_detail.html` usando `namespace` para garantir persistência do status de checkboxes no checklist.
- [x] **Padronização de Timezone**: Substituição sistemática de `datetime.now()` por `now_sp()` em todos os arquivos e endpoints (incluindo Manutenção, Compras, Ativos, etc.) para garantir a correta aplicação do fuso horário `America/Sao_Paulo`.
- [x] **Configuração de Container**: Adicionada a flag `ENV TZ=America/Sao_Paulo` ao `Dockerfile` do ambiente para forçar o timezone local do servidor.
