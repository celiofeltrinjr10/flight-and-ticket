"""Regras de viagem: máximo de escalas e duração máxima de cada voo."""

from __future__ import annotations

from .config import Config
from .models import Itinerary


def fmt_min(m: int) -> str:
    return f"{m // 60}h{m % 60:02d}"


def evaluate(it: Itinerary, cfg: Config) -> Itinerary:
    """Marca o itinerário como válido ou não, com o motivo do descarte."""
    motivos = []
    if it.price is None:
        motivos.append("sem preço")
    if it.stops > cfg.max_escalas:
        motivos.append(f"{it.stops} escalas (máx. {cfg.max_escalas})")
    for s in it.segments:
        if s.duration_min > cfg.max_min_por_trecho:
            motivos.append(
                f"trecho {s.origin}-{s.dest} com {fmt_min(s.duration_min)} "
                f"(máx. {fmt_min(cfg.max_min_por_trecho)})"
            )
    partida_ok, chegada_ok = cfg.aeroportos(it.direction)
    if partida_ok and it.segments[0].origin not in partida_ok:
        motivos.append(f"parte de {it.segments[0].origin}")
    if chegada_ok and it.segments[-1].dest not in chegada_ok:
        motivos.append(f"chega em {it.segments[-1].dest}")
    it.valid = not motivos
    it.reason = "; ".join(motivos)
    return it
