# Rastreador de passagens Barcelona ↔ São Paulo

Todo dia, por volta das 7h de Madri, um robô no GitHub busca os preços de passagens
**Barcelona (BCN) → São Paulo (GRU, VCP ou CGH)** para cada dia de ida entre 1/nov e 23/dez/2026, e da
**volta** para cada dia entre 1/jan e 15/fev/2027. Ele guarda tudo num histórico e publica um
dashboard que abre no celular ou no computador.

Regras aplicadas a todas as opções:
- no máximo **1 escala**;
- **nenhum voo individual com mais de 16 horas**;
- 1 adulto, classe econômica, preços em euros.

Tudo isso, além das datas, das companhias em destaque (LATAM direto e Royal Air Maroc via
Casablanca), da data-limite de chegada (29/12/2026) e dos pesos do score, pode ser mudado no
arquivo [`config.yaml`](config.yaml).

---

## Passo a passo para colocar no ar (feito uma vez só)

Você vai precisar de uma conta gratuita no GitHub. São uns 15 minutos.

### 1. Criar o repositório
1. Entre em https://github.com e faça login (ou crie a conta).
2. Clique no **+** no canto superior direito → **New repository**.
3. Em *Repository name*, escreva `voos-bcn-sp`.
4. Marque **Public**. No plano gratuito, o GitHub Pages só funciona com repositório público.
   O repositório guarda apenas preços de voos, sem dados pessoais.
5. **Não** marque "Add a README" nem nenhuma outra opção. Clique em **Create repository**.

### 2. Enviar os arquivos
Opção mais simples, pelo aplicativo **GitHub Desktop** (https://desktop.github.com):
1. Instale o aplicativo e faça login com a sua conta.
2. **File → Add local repository…** → escolha a pasta `C:\Users\Usuario\voos-bcn-sp`.
3. Clique em **Publish repository**. Desmarque "Keep this code private" e confirme o nome `voos-bcn-sp`.

Ou pelo terminal, se preferir (troque `SEU-USUARIO` pelo seu usuário do GitHub):
```bash
git -C C:/Users/Usuario/voos-bcn-sp remote add origin https://github.com/SEU-USUARIO/voos-bcn-sp.git
```
```bash
git -C C:/Users/Usuario/voos-bcn-sp push -u origin main
```

### 3. Permitir que o robô salve os dados
1. No repositório, vá em **Settings → Actions → General**.
2. Em *Workflow permissions*, marque **Read and write permissions** e clique em **Save**.

### 4. Ativar o site (GitHub Pages)
1. Ainda em **Settings**, clique em **Pages** no menu da esquerda.
2. Em *Build and deployment → Source*, escolha **Deploy from a branch**.
3. Em *Branch*, escolha **main** e a pasta **/docs**. Clique em **Save**.
4. Em 1 ou 2 minutos aparece o endereço: `https://SEU-USUARIO.github.io/voos-bcn-sp/`.
   Salve esse link nos favoritos do celular.

### 5. Rodar a primeira coleta agora (sem esperar o dia seguinte)
1. Vá na aba **Actions**. Se aparecer um aviso, clique em **I understand my workflows, go ahead and enable them**.
2. Clique em **Coleta diária** → **Run workflow** → **Run workflow**.
3. Leva uns 20 minutos. Quando ficar verde ✅, o dashboard é atualizado sozinho.
   Se ficar vermelho ❌, clique na execução e depois em *Coletar preços* para ver o erro.
   O GitHub também manda um e-mail quando uma execução falha.

A partir daí, roda sozinho todo dia.

### 6. (Opcional) Chaves de fontes pagas
Só se um dia for preciso trocar de fonte (veja "Limitações").
1. **Settings → Secrets and variables → Actions → New repository secret**.
2. Nome `SERPAPI_KEY`, valor = a chave criada em https://serpapi.com. Clique em **Add secret**.
3. No `config.yaml`, troque `etapa_a:` e/ou `etapa_b:` para `serpapi`.

---

## Busca sob demanda (outras cidades e datas)

Para pesquisar qualquer outra rota sem mexer no acompanhamento diário:
1. No GitHub (site ou app do celular), abra **Actions → Busca sob demanda → Run workflow**.
2. Preencha:
   - **origem e destino** com 3 letras: aeroporto (`BCN`, `GRU`) ou cidade (`LON`, `PAR`, `MIL`, `NYC`, `SAO`, `RIO`), que cobre todos os aeroportos da cidade;
   - **ida** como `2026-11-10` ou `2026-11-01 a 2026-11-15`;
   - **volta** igual, ou vazia para só ida;
   - adultos, classe, máximo de escalas, moeda e, se quiser, data-limite de chegada.
3. Clique em **Run workflow**. Leva ~1 minuto a cada 8 datas (máximo de 150 datas por busca).
4. O resultado aparece em `https://SEU-USUARIO.github.io/voos-bcn-sp/buscas/`, cada busca com seu próprio
   dashboard. Rodar a mesma busca de novo atualiza a página e acumula histórico.

Os dados ficam em `data/buscas/<rota_datas>/`. A coleta diária continua igual e só usa o `config.yaml`.

## Como funciona

**Etapa A (99 buscas por dia):** para cada data de ida e de volta, busca passagens só de ida no Google
Flights, com até 1 escala. O código de cidade `SAO` cobre GRU, VCP e CGH numa busca só. Cada opção é
guardada com companhia(s), números de voo, rota, duração de cada voo, tempo de conexão, duração total,
preço, fonte, hora da consulta e link para o Google Flights. Depois os filtros (escalas e 16h por voo)
marcam cada opção como válida ou descartada, sempre com o motivo.

**Etapa B (20 buscas por dia):** com os resultados da Etapa A, monta as combinações ida+volta de melhor
score (sempre com vagas para LATAM direto e Royal Air Maroc) e consulta o **preço real da passagem de
ida e volta**, que muitas vezes é bem mais barata que dois trechos separados. No teste de 20/out/2026,
LATAM 10/nov + 25/jan custava 1.670 € em dois trechos e 1.244 € como ida e volta. O dashboard mostra
as duas cifras.

**"Calendário de preços" (matriz de datas):** avaliado e descartado. Desde ago/2026 o Google protege
essa consulta, que só funciona dentro da própria página, e ela também não respeitaria a regra das 16h.
A matriz ida × volta do dashboard é montada com os dados da Etapa A, que já cobrem todas as datas.

**Pausas e falhas:** 4 a 8 segundos entre buscas. Uma busca que falha é repetida até 3 vezes, com
espera crescente (15 s, 45 s…). Se ainda assim falhar, o erro é registrado e a coleta segue para a
próxima data. Para quando houver 8 falhas seguidas (provável bloqueio). Se a fonte principal falhar,
tenta a reserva (navegador).

**Histórico:** cada execução cria uma pasta nova em `data/runs/AAAA-MM-DD_HHMM/` e nada é
sobrescrito:
- `oneway.csv`: todas as opções da Etapa A, inclusive as descartadas e o motivo;
- `roundtrip.csv`: as combinações da Etapa B;
- `errors.csv`: cada tentativa que deu erro;
- `meta.json`: resumo (buscas, falhas, fontes, horário).

O dashboard (`docs/index.html`) é regenerado a partir dessas pastas. As tendências usam a última coleta
de cada dia. Cada dia ocupa uns 200 KB, então a temporada inteira cabe com folga no GitHub.

## O dashboard
1. **Cabeçalho**: data e hora da última atualização, fontes, número de buscas e falhas.
2. **Calendários (ida e volta)**: cada dia colorido do mais barato (verde) ao mais caro (vermelho), com
   preço e companhia. Passe o mouse ou toque num dia para ver as 3 melhores opções. ● = ida que chega até
   a data-limite; ▲▼ = subiu ou caiu desde a coleta anterior.
3. **Matriz ida × volta** com o preço total estimado de cada par de datas (○ = conferido na Etapa B).
4. **Comparador**: LATAM direto × Royal Air Maroc × melhor outra companhia, por data.
5. **Top 10** pelo score, que combina preço, duração total e tempo de conexão (pesos no `config.yaml`).
6. **Ida e volta conferida**: soma dos trechos × preço real de ida e volta.
7. **Tendência**: evolução do menor preço e as datas que mais subiram ou caíram, desde ontem e desde 7
   dias atrás.
8. **Filtros**: companhia, direto ou 1 escala, duração máxima, só idas antes da data-limite.
9. **Resumo do dia**: dia da semana mais barato, datas que caíram mais de 10%, diferença média entre
   LATAM e RAM, economia da ida e volta.

## Rodar no seu computador
Precisa do Python 3.10 ou mais novo (https://www.python.org).
```bash
cd C:/Users/Usuario/voos-bcn-sp
```
```bash
python -m venv .venv
```
```bash
.venv/Scripts/python -m pip install -r requirements.txt
```
```bash
.venv/Scripts/python -m playwright install chromium
```
```bash
.venv/Scripts/python -m tracker.collect --poc
```
```bash
.venv/Scripts/python -m tracker.collect
```
```bash
.venv/Scripts/python -m tracker.build_dashboard
```
- O primeiro `collect` (com `--poc`) é a prova de conceito: 3 idas + 3 voltas, com todos os dados
  impressos na tela. Ele grava em `data/poc/`, que não entra no histórico.
- O segundo `collect` é a coleta completa, de uns 15 a 20 minutos.
- Depois é só abrir `docs/index.html` no navegador.
- Testes dos filtros: `.venv/Scripts/python -m unittest discover -s tests -t .`

## Fontes de dados e limitações

| Fonte (`config.yaml`) | O que é | Custo | Limitações |
|---|---|---|---|
| `google_ff` (principal, Etapa A) | Biblioteca [fast-flights](https://github.com/AWeirdDev/flights) 3.1.0: lê a página do Google Flights por HTTP | Grátis | Não é API oficial. **Pode quebrar se o Google mudar o site.** O Google pode bloquear o endereço de onde vêm as buscas, sobretudo de servidores como os do GitHub. Traz só as ~8 a 10 opções que o Google mostra primeiro. |
| `google_browser` (Etapa B e reserva da A) | Abre o Google Flights num Chrome invisível (Playwright) | Grátis | Mesmos riscos do anterior, e mais lento (~6 s por página). É o único jeito gratuito de obter o preço real de ida e volta. |
| `serpapi` | [SerpApi Google Flights API](https://serpapi.com/google-flights-api): serviço pago que faz a coleta e entrega dados estruturados | Pago por busca (há plano grátis pequeno) | Estável e sem bloqueios, mas 99 + 40 buscas por dia exigem plano pago. Código pronto, **não testado** sem chave. |
| `ignav` | API da Ignav | — | Só o espaço reservado. Precisa da documentação e de uma chave para implementar. |

Outras observações:
- Detalhes técnicos que vale saber se algo quebrar:
  - O fast-flights 3.1.0 ignora o bloco "melhores voos" do Google e não devolve números de voo. Por isso
    a leitura do resultado é feita pelo nosso código (`tracker/gflights.py`), e é ali que o conserto
    acontece se o Google mudar o formato.
  - O pacote também esquece a dependência `typing_extensions`, que já está no `requirements.txt`.
- Da Espanha (UE), o Google mostra primeiro o aviso de cookies. O coletor responde "rejeitar tudo"
  (só cookies essenciais) para chegar aos resultados.
- Preços mudam a toda hora e podem variar entre a consulta e a compra. Confirme sempre no link.
- O GitHub pode atrasar o horário agendado em alguns minutos. Em repositórios públicos, ele desliga
  agendamentos depois de 60 dias sem nenhuma atividade. Os commits diários do robô devem evitar isso,
  mas se a coleta parar, reative em **Actions**.

### Se a coleta começar a falhar
1. Abra **Actions** → a execução vermelha → passo *Coletar preços* e leia o erro.
2. "tela de consentimento" ou "página sem o bloco de resultados": o Google mudou a página. O ajuste é
   em `tracker/gflights.py`.
3. "tráfego incomum", "429" ou muitas falhas seguidas: o Google está bloqueando os servidores do GitHub.
   As saídas, da mais simples à mais robusta:
   - aumentar `pausa_min_s` e `pausa_max_s`;
   - pôr `etapa_a: google_browser`;
   - usar a SerpApi (passo 6).

## Estrutura
```
config.yaml                    tudo que é configurável
tracker/collect.py             coleta (etapas A e B, pausas, novas tentativas, gravação)
tracker/providers/             fontes de dados (interface comum em base.py)
tracker/gflights.py            leitura das páginas do Google Flights
tracker/filters.py             regras de escalas e de 16h por voo
tracker/scoring.py             score do Top 10
tracker/build_dashboard.py     gera docs/index.html
tracker/dashboard_template.html  layout do dashboard
data/runs/                     histórico (uma pasta por coleta)
docs/index.html                dashboard publicado no GitHub Pages
.github/workflows/coleta-diaria.yml  agendamento diário
```
