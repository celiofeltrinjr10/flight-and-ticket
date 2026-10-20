"""Leitura do config.yaml."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SEAT_CODES = {"economy": 1, "premium-economy": 2, "business": 3, "first": 4}


@dataclass
class Highlight:
    id: str
    nome: str
    companhias: list[str]
    somente_direto: bool = False
    via: str | None = None


@dataclass
class Config:
    origem: str
    destino: str
    aeroportos_origem: list[str]
    aeroportos_destino: list[str]
    ida: tuple[date, date]
    volta: tuple[date, date] | None  # None = busca só de ida
    adultos: int
    classe: str
    moeda: str
    data_limite_chegada: date | None
    max_escalas: int
    max_min_por_trecho: int
    destaques: list[Highlight]
    pesos: dict[str, float]
    fonte_a: str
    fonte_a_reserva: str | None
    fonte_b: str
    combinacoes: int
    vagas_por_destaque: int
    max_por_data: int
    max_por_par_de_voos: int
    pausa: tuple[float, float]
    tentativas: int
    espera_base_s: float
    max_falhas_seguidas: int
    poc_ida: list[date] = field(default_factory=list)
    poc_volta: list[date] = field(default_factory=list)
    # Na prova de conceito o limite de escalas não é pedido ao Google, para
    # que o nosso filtro tenha o que descartar e possa ser conferido.
    filtro_no_servidor: bool = True

    @property
    def max_escalas_servidor(self) -> int | None:
        return self.max_escalas if self.filtro_no_servidor else None

    raw: dict = field(default_factory=dict)  # config original (gravado com cada busca)

    @property
    def direcoes(self) -> list[str]:
        return ["ida", "volta"] if self.volta else ["ida"]

    def dias(self, direcao: str) -> list[date]:
        rng = self.ida if direcao == "ida" else self.volta
        if not rng:
            return []
        ini, fim = rng
        return [ini + timedelta(d) for d in range((fim - ini).days + 1)]

    def rota(self, direcao: str) -> tuple[str, str]:
        """(origem, destino) da busca nesta direção."""
        return (self.origem, self.destino) if direcao == "ida" else (self.destino, self.origem)

    def aeroportos(self, direcao: str) -> tuple[list[str], list[str]]:
        """(aeroportos de partida aceitos, aeroportos de chegada aceitos)."""
        if direcao == "ida":
            return self.aeroportos_origem, self.aeroportos_destino
        return self.aeroportos_destino, self.aeroportos_origem

    def destaque(self, itinerario) -> Highlight | None:
        """Primeiro destaque cujo critério o itinerário cumpre."""
        for h in self.destaques:
            if not set(itinerario.airlines) <= set(h.companhias):
                continue
            if h.somente_direto and itinerario.stops != 0:
                continue
            if h.via and h.via not in itinerario.connection_airports:
                continue
            return h
        return None


def _d(v) -> date:
    return v if isinstance(v, date) else date.fromisoformat(str(v))


def load(path: Path | str | None = None) -> Config:
    return from_dict(yaml.safe_load(Path(path or ROOT / "config.yaml").read_text(encoding="utf-8")))


def from_dict(raw: dict) -> Config:
    v, f, fo, b, c = raw["viagem"], raw["filtros"], raw["fontes"], raw["etapa_b"], raw["coleta"]
    poc = raw.get("prova_de_conceito") or {}
    if v["classe"] not in SEAT_CODES:
        raise ValueError(f"classe inválida: {v['classe']}")
    return Config(
        origem=v["origem"],
        destino=v["destino"],
        aeroportos_origem=v.get("aeroportos_origem") or [],
        aeroportos_destino=v.get("aeroportos_destino") or [],
        ida=(_d(v["ida"]["inicio"]), _d(v["ida"]["fim"])),
        volta=(_d(v["volta"]["inicio"]), _d(v["volta"]["fim"])) if v.get("volta") else None,
        adultos=int(v["adultos"]),
        classe=v["classe"],
        moeda=v["moeda"],
        data_limite_chegada=_d(v["data_limite_chegada"]) if v.get("data_limite_chegada") else None,
        max_escalas=int(f["max_escalas"]),
        max_min_por_trecho=int(float(f["max_horas_por_trecho"]) * 60),
        destaques=[Highlight(**h) for h in raw.get("destaques") or []],
        pesos={k: float(x) for k, x in raw["score"].items()},
        fonte_a=fo["etapa_a"],
        fonte_a_reserva=fo.get("etapa_a_reserva") or None,
        fonte_b=fo["etapa_b"],
        combinacoes=int(b["combinacoes"]),
        vagas_por_destaque=int(b["vagas_por_destaque"]),
        max_por_data=int(b["max_por_data"]),
        max_por_par_de_voos=int(b.get("max_por_par_de_voos", 2)),
        pausa=(float(c["pausa_min_s"]), float(c["pausa_max_s"])),
        tentativas=int(c["tentativas"]),
        espera_base_s=float(c["espera_base_s"]),
        max_falhas_seguidas=int(c["max_falhas_seguidas"]),
        poc_ida=[_d(x) for x in poc.get("ida") or []],
        poc_volta=[_d(x) for x in poc.get("volta") or []],
        raw=raw,
    )
