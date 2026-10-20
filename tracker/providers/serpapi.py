"""Fonte paga e estável: SerpApi Google Flights API (https://serpapi.com/google-flights-api).

Ativação: crie a chave em serpapi.com e salve como segredo SERPAPI_KEY no
GitHub (ou variável de ambiente local). Depois troque a fonte no config.yaml.
Cada busca consome 1 crédito; a ida e volta usa 2 (ida + lista de voltas).
Ainda não testada com chave real neste projeto.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone

from ..config import SEAT_CODES
from ..models import Itinerary, Segment
from .base import Provider, ProviderError, RoundTripQuote

API = "https://serpapi.com/search.json"


class SerpApi(Provider):
    name = "serpapi"
    supports_roundtrip = True

    def __init__(self, cfg):
        super().__init__(cfg)
        self.key = os.environ.get("SERPAPI_KEY")
        if not self.key:
            raise ProviderError("variável de ambiente SERPAPI_KEY não definida")

    def _airports(self, direction: str) -> tuple[str, str]:
        dep, arr = self.cfg.aeroportos(direction)
        return ",".join(dep), ",".join(arr)

    def _get(self, **params) -> dict:
        cfg = self.cfg
        base = {
            "engine": "google_flights", "api_key": self.key, "currency": cfg.moeda, "hl": "en",
            "adults": cfg.adultos, "travel_class": SEAT_CODES[cfg.classe],
            # stops: 1 = só direto, 2 = até 1 escala, 3 = até 2 escalas, 0 = qualquer
            "stops": 0 if cfg.max_escalas_servidor is None else cfg.max_escalas_servidor + 1,
        }
        url = API + "?" + urllib.parse.urlencode({**base, **params})
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                data = json.load(r)
        except Exception as e:
            raise ProviderError(f"SerpApi: {e}") from e
        if "error" in data and not data.get("best_flights") and not data.get("other_flights"):
            if "no results" in str(data["error"]).lower():
                return {}
            raise ProviderError(f"SerpApi: {data['error']}")
        return data

    def _parse(self, data: dict, direction: str, day: date, queried_at) -> list[Itinerary]:
        link = (data.get("search_metadata") or {}).get("google_flights_url", "")
        out = []
        for opt in (data.get("best_flights") or []) + (data.get("other_flights") or []):
            segs = []
            for f in opt["flights"]:
                code, _, num = (f.get("flight_number") or "").partition(" ")
                segs.append(Segment(
                    origin=f["departure_airport"]["id"], dest=f["arrival_airport"]["id"],
                    departure=datetime.strptime(f["departure_airport"]["time"], "%Y-%m-%d %H:%M"),
                    arrival=datetime.strptime(f["arrival_airport"]["time"], "%Y-%m-%d %H:%M"),
                    duration_min=int(f["duration"]), airline=code, number=num,
                    airline_name=f.get("airline", ""), aircraft=f.get("airplane", ""),
                ))
            it = Itinerary(
                direction=direction, date=day, segments=segs,
                layovers_min=[int(x["duration"]) for x in opt.get("layovers") or []],
                total_min=int(opt["total_duration"]), price=opt.get("price"),
                currency=self.cfg.moeda, source=self.name, queried_at=queried_at, link=link,
                airline_names=list(dict.fromkeys(s.airline_name for s in segs)),
            )
            it._serp = opt  # guarda o departure_token para a ida e volta
            out.append(it)
        return out

    def search_oneway(self, direction: str, day: date) -> list[Itinerary]:
        dep, arr = self._airports(direction)
        now = datetime.now(timezone.utc)
        data = self._get(departure_id=dep, arrival_id=arr, outbound_date=day.isoformat(), type=2)
        return self._parse(data, direction, day, now)

    def search_roundtrip(self, outbound: Itinerary, return_day: date) -> list[RoundTripQuote]:
        dep, arr = self._airports("ida")
        params = dict(departure_id=dep, arrival_id=arr, outbound_date=outbound.date.isoformat(),
                      return_date=return_day.isoformat(), type=1)
        now = datetime.now(timezone.utc)
        outs = self._parse(self._get(**params), "ida", outbound.date, now)
        match = next((o for o in outs if o.flights == outbound.flights), None)
        if match is None:
            return []
        token = match._serp.get("departure_token")
        if not token:
            return []
        rets = self._parse(self._get(**params, departure_token=token), "volta", return_day, now)
        return [RoundTripQuote(total_price=r.price, ret=r, link=r.link) for r in rets if r.price]
