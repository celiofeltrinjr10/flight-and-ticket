# App de busca de passagens — regras do projeto

> Este projeto não tem relação com o Liner Notes nem com o comitê de investimentos.
> Ignore os `CLAUDE.md` de pastas acima desta.

## Quem é quem
- **Celio — fundador.** Decide o que é o produto e **autoriza tudo o que vai ao ar**.
- **Sessão principal — Head/CTO.** Planeja, coordena os agentes, escreve e revisa código, e leva cada
  entrega ao Celio para aprovação.
- **Agentes** (`.claude/agents/`): `produto`, `design`, `dados`, `qa`. Cada um tem função fixa; agentes não
  chamam outros agentes — a sessão principal chama cada um e repassa os caminhos dos arquivos.

## O que é o produto
Ver `produto/BRIEF.md`. Em resumo: app público que responde "quando voar?", "qual opção?" e
"compro agora ou espero?", com o preço final real.

## Como uma mudança vai ao ar
1. Toda mudança de código ou layout é feita num branch e vira um Pull Request no GitHub.
2. Antes de pedir aprovação: testes passando, `qa` revisou, capturas de tela (celular e computador) enviadas
   ao Celio.
3. Só depois de um "ok" explícito do Celio no chat o PR é integrado ao `main` (que publica o site).
4. Exceção: a coleta diária automática grava dados direto no `main` — isso não é mudança de produto.

## Regras invioláveis
1. **Nunca inventar preço.** Todo número vem de uma coleta registrada, com fonte e data/hora.
   Estimativas aparecem sempre marcadas (≈) e com o método explicado.
2. **Menos texto.** Título curto + no máximo uma linha de apoio por seção. Explicações longas ficam
   recolhidas. Na dúvida, cortar.
3. **Sem credenciais no repositório.** Chaves de API só como segredos do GitHub/Vercel.
4. **Fonte de dados para o público tem de ser licenciada** (decisão D1 do brief). A leitura do site do
   Google é só para uso pessoal e testes.
5. Legal UE/Espanha antes de abrir ao público: privacidade, cookies, termos, aviso legal.

## Tecnologia atual
- Python 3.12 (`tracker/`), coleta diária e busca sob demanda pelo GitHub Actions, dados em CSV em `data/`,
  páginas estáticas em `docs/` publicadas no GitHub Pages.
- Testes: `python -m unittest discover -s tests -t .`
- Dashboard: `python -m tracker.build_dashboard` (template em `tracker/dashboard_template.html`, copiado para `painel.html`).
- Site (Vercel): Next.js na raiz (`app/`, `lib/`), lê `data/public/*.json` do GitHub. `npm run build` para testar.

## Estilo
Português do Brasil, linguagem direta. Celio não é programador: explicar mudanças em linguagem simples.
Valores em EUR.
