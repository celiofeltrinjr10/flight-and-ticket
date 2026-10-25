"""Fonte principal: Google Flights via biblioteca fast-flights (HTTP simples, rápido).

O fast-flights monta a consulta e o cliente HTTP que imita o Chrome. A leitura
do resultado é nossa (``gflights.py``) porque o leitor da biblioteca, na 3.1.0,
ignora o bloco "melhores voos" e não devolve número de voo nem conexões.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from fast_flights import FlightQuery, Passengers, create_query
from primp import Client

from .. import gflights
from ..models import Itinerary
from .base import Provider, ProviderError

URL = "https://www.google.com/travel/flights"


class GoogleFastFlights(Provider):
    name = "google_fast_flights"

    def __init__(self, cfg):
        super().__init__(cfg)
        self.client = Client(
            impersonate="chrome_145", impersonate_os="macos", referer=True, cookie_store=True,
        )

    def search_oneway(self, direction: str, day: date) -> list[Itinerary]:
        cfg = self.cfg
        origin, dest = cfg.rota(direction)
        q = create_query(
            flights=[FlightQuery(date=day.isoformat(), from_airport=origin, to_airport=dest,
                                 max_stops=cfg.max_escalas_servidor)],
            seat=cfg.classe, trip="one-way", passengers=Passengers(adults=cfg.adultos),
            language="en", currency=cfg.moeda,
        )
        queried_at = datetime.now(timezone.utc)
        try:
            resp = self.client.get(
                URL, params=q.params(),
                headers={"Cookie": f"{gflights.CONSENT_COOKIE_NAME}={gflights.CONSENT_COOKIE_VALUE}"},
            )
        except Exception as e:  # erro de rede
            raise ProviderError(f"rede: {e}") from e
        if resp.status_code == 429:
            raise gflights.Blocked("HTTP 429 (muitas requisições)")
        if resp.status_code >= 400:
            raise ProviderError(f"HTTP {resp.status_code}")
        payload = gflights.page_payload(resp.text)
        link = q.url()
        out = []
        for row in gflights.raw_rows(payload):
            try:
                out.append(gflights.row_to_itinerary(
                    row, direction=direction, day=day, source=self.name,
                    queried_at=queried_at, currency=cfg.moeda, link=link,
                ))
            except (IndexError, TypeError, ValueError) as e:
                raise ProviderError(f"formato inesperado do Google: {e}") from e
        if not out:
            raise gflights.EmptyResult("o Google respondeu sem nenhum voo para esta data")
        return out
