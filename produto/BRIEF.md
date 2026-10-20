# Brief do produto

> Versão 1 · 20/10/2026 · aprovado por: _pendente (Celio)_

## Em uma frase
O app de passagens que diz **quando voar, qual opção comprar e se é melhor comprar agora ou esperar** — com o preço final real e sem letras miúdas.

## Para quem (primeiro público)
Quem mora na Europa e voa para o Brasil (e vice-versa) com datas flexíveis: semanas de janela, não ±3 dias.
Começar por um corredor estreito e bem servido (Europa ↔ Brasil) e expandir rota a rota.

## As 3 perguntas que o app responde
1. **Quando voar?** As datas mais baratas dentro de uma janela grande, de ida e de volta.
2. **Qual opção?** O preço final real: ida e volta juntas ou duas passagens, o que for mais barato,
   respeitando o conforto que a pessoa escolhe (escalas, horas máximas por voo, horário).
3. **Compro agora ou espero?** Um sinal claro, com o motivo explicado e o grau de confiança.

## Por que somos diferentes
| Hoje (Google Flights, Skyscanner, Kayak, Hopper) | Nós |
|---|---|
| Janela de ±3 dias | Janelas de semanas, ida e volta |
| Preço de ida e volta ou de trechos, um de cada vez | Compara os dois e mostra o menor como preço final |
| Filtros genéricos | Regras de conforto (ex.: nenhum voo acima de 16h) |
| "Previsão" opaca | Sinal "comprar ou esperar" com histórico e explicação |

## Fora da versão 1
Venda ou reserva dentro do app (redirecionamos para quem vende), hotéis, multi-cidades, pagamentos.

## Como o app pode gerar receita (hipóteses a validar)
- Comissão de afiliado nos cliques para reservar.
- Plano pago com alertas ilimitados e mais rotas acompanhadas.

## Como saber se está funcionando
Buscas por semana · alertas criados · cliques para reservar · acerto do "comprar ou esperar" (o preço subiu
depois de dizermos "compre"?).

## Riscos principais
1. **Fonte de dados.** Ler o site do Google serve para uso pessoal, não para um app público (termos de uso
   e bloqueio). Precisamos de uma fonte licenciada → decisão D1.
2. **Custo por busca** das fontes pagas → decisão D4.
3. **"Comprar ou esperar" precisa de histórico.** Começamos acumulando dados das rotas acompanhadas.
4. **Legal (UE/Espanha):** política de privacidade, cookies, termos, aviso legal antes de abrir ao público.

## Decisões do fundador (pendentes)
| # | Decisão | Quando |
|---|---|---|
| D1 | Fonte de dados licenciada | Antes da Fase 3 |
| D2 | Nome e marca | Antes do lançamento |
| D3 | Modelo de receita | Antes do lançamento |
| D4 | Orçamento mensal (dados + hospedagem) | Junto com D1 |

## Roteiro
| Fase | Entrega | Situação |
|---|---|---|
| 0 | Este brief | aguardando aprovação |
| 1 | Organização: regras, agentes, lista de tarefas, fluxo de aprovação | em andamento |
| 2 | Tela única, limpa, no formato atual | proposta para aprovação |
| 3 | App: site Next.js na Vercel + banco de dados + busca direto no app | planejar após D1/D4 |
| 4 | Dados confiáveis: fonte licenciada, monitoramento, alertas de falha | — |
| 5 | Alertas de preço, rotas salvas, "comprar ou esperar" | — |
| 6 | Lançamento público: domínio, páginas legais, analytics, plano pago da Vercel | — |
