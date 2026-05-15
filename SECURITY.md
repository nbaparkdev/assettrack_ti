# Política de Segurança - AssetTrack TI

A segurança da aplicação AssetTrack TI e dos dados de nossos usuários é nossa prioridade.

## Versões Suportadas

Atualmente, apenas a versão mais recente da branch principal (main) recebe atualizações de segurança.

| Versão | Suportada |
| :--- | :--- |
| v1.x (Main) | ✅ Sim |
| < 1.0 | ❌ Não |

## Práticas de Segurança Implementadas

O AssetTrack TI foi construído com as seguintes camadas de proteção:

1.  **Autenticação JWT:** Uso de JSON Web Tokens com expiração configurável para sessões seguras.
2.  **Hashing de Senhas:** Todas as senhas são armazenadas utilizando o algoritmo `Bcrypt` (via `passlib`).
3.  **Controle de Acesso (RBAC):** Diferenciação de permissões entre Usuários, Técnicos e Administradores.
4.  **Rate Limiting:** Proteção contra ataques de força bruta e DoS nos endpoints de autenticação e geração de QR Code (limite de 10 tentativas/min).
5.  **Validação de Dados:** Uso rigoroso de Pydantic para garantir que apenas dados válidos entrem no sistema.
6.  **Isolamento via Docker:** Execução em containers para mitigar riscos de comprometimento do host.

## Como Relatar uma Vulnerabilidade

Se você descobrir uma vulnerabilidade de segurança, por favor **NÃO** abra uma issue pública. Em vez disso, siga o procedimento abaixo:

1.  Envie um e-mail para o responsável pelo projeto (Humberto) ou utilize o canal de comunicação interna da empresa.
2.  Descreva detalhadamente a vulnerabilidade e os passos para reproduzi-la.
3.  Aguarde uma resposta antes de divulgar qualquer informação publicamente.

Prometemos analisar e responder a todos os relatos de segurança em até 48 horas úteis.

## Melhores Práticas Recomendadas para Operação

- **Mude o SECRET_KEY:** Sempre altere a variável `SECRET_KEY` no arquivo `.env` ao implantar em produção.
- **Use HTTPS:** Recomendamos o uso de um Proxy Reverso (como Nginx ou Traefik) com certificados SSL/TLS na frente da aplicação.
- **Mantenha o Docker atualizado:** Verifique regularmente se há atualizações para as imagens base do Python e PostgreSQL.
