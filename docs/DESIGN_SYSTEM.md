# AssetTrack Board — padrão visual

## Identidade

O sistema usa uma linguagem visual inspirada em quadros operacionais: fundo azul em gradiente, superfícies brancas translúcidas, títulos em azul-marinho e azul `#0C66E4` como ação principal.

| Uso | Cor |
| --- | --- |
| Navegação e ação principal | `#0C66E4` |
| Texto e contraste | `#172B4D` |
| Texto auxiliar | `#5E6C84` |
| Fundo/painéis | `#7BB7DF` / branco translúcido |
| Sucesso, atenção, crítico, especial | verde, laranja, vermelho e roxo existentes |

## Componentes e manutenção

- `index.css` contém os tokens Tailwind e a camada compartilhada `app-content`, que atualiza cartões, tabelas, campos e transições das telas legadas de forma consistente.
- `Header.tsx` é a barra superior compacta: início, projetos, busca, ações, alertas e perfil.
- `Sidebar.tsx` oferece a navegação por módulos com estados ativos em formato de cartão.
- Para novas telas, use os tokens `brand-*`, cartões `bg-brand-card border border-brand-border`, cantos de 12–16px e ações `bg-brand-primary`.

O layout é responsivo: o conteúdo reduz o espaçamento e a navegação se adapta em telas menores. Preserve labels, `title` e foco visível ao acrescentar ícones ou ações.
