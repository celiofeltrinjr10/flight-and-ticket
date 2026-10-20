# D1/D4 — Fonte de dados licenciada e orçamento

> Issue: https://github.com/celiofeltrinjr10/voos-bcn-sp/issues/2 · Pesquisa: 20/10/2026 · Decisão: _pendente (Celio)_
> Todas as fontes abaixo foram consultadas em **20/10/2026**. O que não foi encontrado aparece como **não encontrado**.

## Premissas de volume
- Hoje: ~120 buscas só de ida + ~60 conferências de ida e volta por dia = **~180/dia ≈ 5.400/mês** (30 dias).
- 10x: **~54.000/mês**.
- Câmbio para EUR: 1 EUR = 1,1215 USD (taxa de referência do BCE, 20/10/2026 — https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A).
- Custos mensais abaixo são **cálculo** (volume × preço publicado), não cotação. Não incluem hospedagem.

## Resumo em uma linha por fornecedor
| Fornecedor | Aberto a nós hoje? | Licenciado para app público? | Custo/mês hoje | Custo/mês 10x |
|---|---|---|---|---|
| **Duffel** | Sim, autosserviço | Sim (conteúdo de companhias aéreas) | ≈ €24 ($27) | ≈ €241 ($270) |
| **Ignav** | Sim, autosserviço | **Incerto**: origem dos dados não divulgada | ≈ €10 ($10,80) | ≈ €96 ($108) |
| **SerpApi** (Google Flights) | Sim, autosserviço | **Não**: raspa o Google, sem licença do Google | ≈ €134 ($150) | ≈ €646 ($725) |
| **Travelpayouts** (Data API, cache) | Sim, autosserviço | Sim (programa de afiliados) | €0 | €0 |
| **Travelpayouts** (Search API, ao vivo) | **Não**: exige 50 mil usuários/mês | Sim | não encontrado | não encontrado |
| **Skyscanner** (Travel API) | **Não**: exige 100 mil usuários/mês | Sim | sem cobrança publicada (comissão por clique) | idem |
| **Kiwi.com** (Tequila) | **Não**: só por convite desde 30/05/2024 | Sim | não encontrado | não encontrado |
| **Amadeus** for Developers | **Não**: autosserviço desligado em 17/07/2026; só contrato Enterprise | Sim | não encontrado (negociado) | não encontrado |

## Tabela comparativa detalhada

| | Duffel | Ignav | SerpApi (Google Flights) | Travelpayouts Data API | Skyscanner Travel API |
|---|---|---|---|---|---|
| **Situação** | Aberto, "pay as you go", sem taxa inicial [D1] | Aberto, cadastro imediato [I1] | Aberto [S1] | Aberto, basta token de afiliado [T1] | Só por candidatura; mín. 100 mil usuários ativos/mês; não aceita start-ups sem produto [K1] |
| **Tipo de dado** | Ofertas ao vivo, reserváveis | Preços ao vivo + links de compra [I2] | Resultados do Google Flights | **Cache** de buscas de usuários Aviasales, 2–7 dias [T1] (48 h no endpoint por datas [T2]) | Ao vivo (create/poll) [K2] |
| **LATAM** | Sim, listada [D2] | não encontrado (FAQ cita "major carriers" em 80+ mercados [I3]) | Sim — nossa coleta atual via Google tem 189 registros LATAM (`data/`) | depende do que usuários buscaram (não verificado) | não encontrado |
| **Royal Air Maroc** | Sim, via Travelport (GDS) [D3] | não encontrado | Sim — 168 registros RAM na nossa coleta | depende do cache (não verificado) | não encontrado |
| **Nº de voo** | não verificado hoje (conferir no teste) | Sim, por trecho [I2] | Sim, por trecho [S2] | Sim, 1 por oferta [T2] | Sim, por segmento [K2] |
| **Duração por trecho** | não verificado hoje (conferir no teste) | Sim, `duration_minutes` por trecho [I2] | Sim, por trecho + escalas [S2] | Só ida e volta totais (`duration_to/back`) [T2] | Sim [K2] |
| **Preço ida e volta** | Sim (uma busca com 2 trechos) | Sim, endpoint próprio [I2] | Sim, mas detalhar a volta exige 2ª chamada [S2] | Sim (`one_way=false`) [T2] | Sim [K2] |
| **Calendário de datas** | Não encontrado | Sim: até 31 datas = 1 requisição [I2] | Não (1 data por busca) | Sim (mês) [T2] | Só via Indicative Prices [K3] |
| **EUR** | não encontrado (2% de taxa se houver conversão [D1]) | via `market` (ex.: ES); EUR não confirmado [I2] | Sim, parâmetro `currency` [S2] | Sim, parâmetro `currency` (padrão RUB) [T2] | Sim, parâmetro `currency` [K2] |
| **Limites** | sem limite publicado; cobra excesso de busca | sem limite por conta; teto de gasto opcional [I2] | 15 mil/mês e 3 mil/h no plano de $150 [S1] | "API rate limits" (artigo não lido) [T2] | Buscas ao vivo só quando o usuário clica; **coleta automática proibida** [K3] |
| **Preço** | $0,005 por busca acima de 1.500 buscas por reserva; $3 por reserva [D1] | $2 por 1.000 requisições com sucesso; 1.000 grátis uma vez [I1] | Planos fixos: $75 (5 mil), $150 (15 mil), $725 (100 mil) [S1] | Grátis | Sem cobrança publicada; Skyscanner "absorve o custo" se 5–20% das buscas virarem clique [K3] |
| **Contas (hoje / 10x)** | sem reservas, toda busca é excedente: 5.400 × $0,005 = $27 / 54.000 × $0,005 = $270 | 5.400 × $2/1.000 = $10,80 / $108 | ida e volta = 2 buscas → ~7.200–9.000/mês → plano $150 / 72–90 mil → plano $725 | €0 / €0 | — |
| **Exibir preço em app público** | Termos sobre uso só-busca (sem venda): **não encontrado** — confirmar por escrito | Termos permitem publicar e vender os dados, "sem atribuição" — mas "não substituem direitos de terceiros" [I4] | Sem licença do Google. Google processou a SerpApi (dez/2025); caso arquivado em 20/07/2026 com direito a recurso [S3]. Seguro jurídico só nos EUA, planos ≥ $150 [S1] | Recomendado para "páginas de conteúdo"; não usar preço expirado [T1][T2] | Obrigatório "Powered by Skyscanner" e regras de layout [K3] |
| **Receita de afiliado** | Não; receita só vendendo passagem (margem) — fora da v1 | Não encontrado; links levam a companhias/agências sem comissão informada [I2] | Não | Sim: média de ~1,1% do bilhete (página sem data) [T3]; cookie de 30 dias | Sim, por clique (valor não publicado) [K3] |

Outros avaliados e descartados: **Kiwi.com Tequila** — novas parcerias "invitation only" desde 30/05/2024 [KW1]. **Amadeus** — autosserviço desligado em 17/07/2026, só Enterprise com contrato [A1]. **Travelpayouts Search API (ao vivo)** — exige 50.000 usuários ativos/mês confirmados, sem exceção [T4]. **Travelport/Sabre** — contratos enterprise; condições para start-ups: não encontrado. **Atores Apify / APIs no RapidAPI que leem o Google** — mesma situação jurídica da SerpApi, não são licenciadas.

## Finalistas

### A. Duffel (+ Travelpayouts para links de afiliado) — licenciado, ao vivo
- ✅ Conteúdo vem das companhias (LATAM direto; Royal Air Maroc via Travelport). Fonte claramente licenciada.
- ✅ Barato no volume atual (≈ €24/mês) e sem mensalidade.
- ✅ Ida e volta numa só busca (número de voo e duração por trecho a conferir no teste).
- ❌ Feita para **vender** passagem. Uso só para pesquisa (sem reservas) não está claro nos termos → perguntar à Duffel por escrito.
- ❌ Sem calendário de datas: janelas de semanas custam uma busca por data; o custo sobe rápido com usuários (≈ €241/mês a 10x).
- ❌ Mostra o preço da Duffel, não o mais barato do mercado (sem agências online). Receita só vendendo (fora da v1) ou via link de afiliado Travelpayouts à parte.

### B. Ignav — melhor encaixe e mais barata, origem incerta
- ✅ Faz exatamente o que o app precisa: calendário de 31 datas numa requisição, ida e volta, número de voo, duração por trecho.
- ✅ A mais barata (≈ €10/mês hoje, ≈ €96 a 10x) e termos que permitem guardar e publicar os dados (bom para o histórico do "comprar ou esperar").
- ❌ **Não diz de onde vêm os dados** ("multiple proprietary sources") e os termos não nomeiam empresa nem país. Se ela própria lê o Google, herdamos o mesmo risco de hoje.
- ❌ Empresa pequena (contato é um e-mail pessoal): risco de continuidade. Sem receita de afiliado.

### C. SerpApi — mais fácil, mas não cumpre a regra de fonte licenciada
- ✅ Mesmos dados que já usamos (Google Flights), inclusive LATAM e Royal Air Maroc; troca de código mínima.
- ❌ Não é licenciada pelo Google; o seguro jurídico só vale nos EUA. Viola a regra 4 do projeto.
- ❌ A mais cara (≈ €134/mês hoje, ≈ €646 a 10x). Serve só como ponte para testes.

## Recomendação
1. **Duffel como fonte principal na Fase 3**, condicionada a uma confirmação por escrito de que o uso só-busca (sem venda) é permitido. Orçamento D4 de dados: **até ~€25/mês** no volume atual. Somar **Travelpayouts** (grátis) para os links de compra com comissão e como segunda fonte de calendário.
2. **Em paralelo, perguntar à Ignav** (gus@ignav.com) qual a origem e a licença dos dados, e qual a empresa responsável. Se a resposta for satisfatória, a Ignav vira a melhor opção (mais barata e com calendário).
3. **SerpApi não**, exceto como ponte de teste fora do público.
4. **Skyscanner** quando passarmos de 100 mil usuários/mês — dá receita por clique, mas proíbe coleta automática.

Antes de decidir, testar de graça Duffel (modo de teste) e Ignav (1.000 requisições grátis) na rota BCN↔GRU: conferir LATAM, Royal Air Maroc, preço em EUR e se o preço bate com o que coletamos hoje.

## Fontes (consultadas em 20/10/2026)
- [D1] Duffel — preços: https://duffel.com/pricing
- [D2] Duffel — LATAM: https://duffel.com/flights/airlines/latam
- [D3] Duffel — Royal Air Maroc: https://duffel.com/flights/airlines/royal-air-maroc
- [I1] Ignav — preços e resumo: https://ignav.com/llms.txt
- [I2] Ignav — documentação completa: https://ignav.com/llms-full.txt · https://ignav.com/openapi.json
- [I3] Ignav — FAQ: https://ignav.com/docs/faq
- [I4] Ignav — termos (vigentes desde 01/10/2026): https://ignav.com/terms
- [S1] SerpApi — preços: https://serpapi.com/pricing
- [S2] SerpApi — Google Flights API: https://serpapi.com/google-flights-api
- [S3] Processo Google × SerpApi: https://news.bloomberglaw.com/ip-law/google-lawsuit-against-data-scraper-tossed-over-authority-issue · https://www.vktr.com/ai-platforms/google-sues-serpapi-over-data-scraping/
- [T1] Travelpayouts — requisitos Data API: https://support.travelpayouts.com/hc/en-us/articles/203956083-Requirements-for-Aviasales-data-API-access
- [T2] Travelpayouts — Aviasales Data API: https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API
- [T3] Travelpayouts — programa de afiliados Aviasales: https://travelpayouts.com/en/offers/aviasales-affiliate-program
- [T4] Travelpayouts — acesso à Search API: https://support.travelpayouts.com/hc/en-us/articles/210995808-How-to-get-access-to-the-Aviasales-Search-API
- [K1] Skyscanner — critérios da Travel API: https://www.partners.skyscanner.net/contact/travel-api
- [K2] Skyscanner — Flights Live Prices: https://developers.skyscanner.net/docs/flights-live-prices/overview
- [K3] Skyscanner — regras de uso: https://developers.skyscanner.net/docs/getting-started/usage-guidelines
- [KW1] Kiwi.com — nova política de parcerias (30/05/2024): https://media.kiwi.com/articles-and-interviews/better-for-business-kiwi-com-takes-a-new-approach-to-partnerships/
- [A1] PhocusWire, 09/02/2026 — Amadeus encerra o autosserviço: https://www.phocuswire.com/amadeus-shut-down-self-service-apis-portal-developers
- Cobertura LATAM/RAM do Google: contagem nos CSVs de `data/` deste repositório (20/10/2026).
