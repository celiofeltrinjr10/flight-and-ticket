# Rascunhos de e-mail – decisão D1 (fonte de dados)

> Para o Celio revisar e enviar da conta dele. Ajuste o nome do app quando a D2 estiver decidida.

---

## 1. Duffel

**Para:** contato comercial da Duffel (formulário em https://duffel.com/contact-us ou o e-mail de vendas indicado lá)
**Assunto:** Search-only use of the Duffel Flights API for a price comparison app

Hello Duffel team,

I'm building a consumer app that helps travellers between Europe and Brazil decide when to fly and whether
to buy now or wait. It shows prices for flexible date windows (several weeks) and tracks price history for
the routes users follow. We do not plan to sell tickets in the first version; users click through to book.

Before we integrate, could you confirm:

1. Is search-only usage (offer requests without bookings) allowed under your terms? Is there an excess-search
   fee or a look-to-book ratio we should know about?
2. Can we display your fares publicly in the app and store them to build price history?
3. Do offers include flight numbers, per-segment durations and round-trip fares?
4. Coverage: are LATAM (direct BCN–GRU) and Royal Air Maroc (via Casablanca) available for search?
5. Expected volume today: around 5,400 searches per month, possibly 10x within a year. What would the cost be?

Thank you,
Celio Feltrin

---

## 2. Ignav

**Para:** gus@ignav.com
**Assunto:** Questions about Ignav's flight data before integrating

Hi Gus,

I'm building a flight price app for travellers between Europe and Brazil (flexible date windows, price
history, "buy now or wait" signal). Ignav's date-calendar endpoint fits our needs very well. Before we commit,
could you help with a few questions?

1. Where does the flight data come from, and under which licences or agreements? We need to make sure we can
   display it publicly in a consumer app.
2. Which company operates Ignav (legal name and country)?
3. Can we store the prices we receive to build price history over time?
4. Coverage: LATAM direct BCN–GRU and Royal Air Maroc via Casablanca, in EUR?
5. Expected volume today: around 5,400 requests per month, possibly 10x within a year.

Thanks a lot,
Celio Feltrin
