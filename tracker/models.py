"""Estruturas de dados comuns a todas as fontes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Segment:
    """Um voo individual (decolagem -> pouso)."""

    origin: str
    dest: str
    departure: datetime  # hora local do aeroporto de partida
    arrival: datetime  # hora local do aeroporto de chegada
    duration_min: int
    airline: str  # código IATA, ex. "AT"
    number: str  # ex. "965"
    airline_name: str = ""
    aircraft: str = ""

    @property
    def flight(self) -> str:
        return f"{self.airline}{self.number}"


@dataclass
class Itinerary:
    """Uma opção de viagem num sentido (ida ou volta), com 0 ou mais conexões."""

    direction: str  # "ida" | "volta"
    date: date  # data pesquisada
    segments: list[Segment]
    layovers_min: list[int]  # tempo de cada conexão, em minutos
    total_min: int  # da primeira decolagem ao último pouso
    price: float | None
    currency: str
    source: str
    queried_at: datetime
    link: str
    airline_names: list[str] = field(default_factory=list)
    valid: bool = True
    reason: str = ""

    @property
    def stops(self) -> int:
        return len(self.segments) - 1

    @property
    def airlines(self) -> list[str]:
        return list(dict.fromkeys(s.airline for s in self.segments))

    @property
    def flights(self) -> str:
        return " ".join(s.flight for s in self.segments)

    @property
    def route(self) -> str:
        return "-".join([self.segments[0].origin] + [s.dest for s in self.segments])

    @property
    def connection_airports(self) -> list[str]:
        return [s.dest for s in self.segments[:-1]]

    @property
    def longest_segment_min(self) -> int:
        return max(s.duration_min for s in self.segments)

    def to_dict(self) -> dict:
        d = {k: getattr(self, k) for k in (
            "direction", "layovers_min", "total_min", "price", "currency", "source", "link",
            "airline_names", "valid", "reason")}
        d["date"] = self.date.isoformat()
        d["queried_at"] = self.queried_at.isoformat()
        d["segments"] = [{**s.__dict__, "departure": s.departure.isoformat(), "arrival": s.arrival.isoformat()}
                         for s in self.segments]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Itinerary":
        segs = [Segment(**{**s, "departure": datetime.fromisoformat(s["departure"]),
                           "arrival": datetime.fromisoformat(s["arrival"])}) for s in d["segments"]]
        return cls(
            direction=d["direction"], date=date.fromisoformat(d["date"]), segments=segs,
            layovers_min=d["layovers_min"], total_min=d["total_min"], price=d["price"],
            currency=d["currency"], source=d["source"], queried_at=datetime.fromisoformat(d["queried_at"]),
            link=d["link"], airline_names=d["airline_names"], valid=d["valid"], reason=d["reason"],
        )


CSV_FIELDS = [
    "run_id", "consultado_em", "fonte", "direcao", "data", "companhias", "companhias_nomes",
    "voos", "rota", "escalas", "partida", "chegada", "trechos_min", "maior_trecho_min",
    "conexoes_min", "duracao_total_min", "preco", "moeda", "valido", "motivo", "link",
]


def to_row(it: Itinerary, run_id: str) -> dict:
    return {
        "run_id": run_id,
        "consultado_em": it.queried_at.isoformat(timespec="seconds"),
        "fonte": it.source,
        "direcao": it.direction,
        "data": it.date.isoformat(),
        "companhias": "+".join(it.airlines),
        "companhias_nomes": " + ".join(it.airline_names),
        "voos": it.flights,
        "rota": it.route,
        "escalas": it.stops,
        "partida": it.segments[0].departure.isoformat(timespec="minutes"),
        "chegada": it.segments[-1].arrival.isoformat(timespec="minutes"),
        "trechos_min": "|".join(str(s.duration_min) for s in it.segments),
        "maior_trecho_min": it.longest_segment_min,
        "conexoes_min": "|".join(str(x) for x in it.layovers_min),
        "duracao_total_min": it.total_min,
        "preco": "" if it.price is None else f"{it.price:.0f}",
        "moeda": it.currency,
        "valido": int(it.valid),
        "motivo": it.reason,
        "link": it.link,
    }
