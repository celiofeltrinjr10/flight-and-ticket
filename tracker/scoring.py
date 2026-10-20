"""Score de combinações ida+volta: 0 a 100, maior é melhor.

Cada critério (preço, duração total, tempo de conexão) é reescalado entre o
melhor e o pior valor do conjunto (0 = melhor, 1 = pior); o score é a média
ponderada pelos pesos do config.yaml, convertida para 100 = melhor em tudo.
O dashboard usa a mesma fórmula em JavaScript.
"""

from __future__ import annotations

from .models import Itinerary


def combo_metrics(out: Itinerary, ret: Itinerary) -> tuple[float, int, int]:
    return (
        out.price + ret.price,
        out.total_min + ret.total_min,
        sum(out.layovers_min) + sum(ret.layovers_min),
    )


def score(rows: list[tuple[float, float, float]], pesos: dict[str, float]) -> list[float]:
    if not rows:
        return []
    w = (pesos.get("preco", 0), pesos.get("duracao_total", 0), pesos.get("conexao", 0))
    total_w = sum(w) or 1
    lo = [min(r[i] for r in rows) for i in range(3)]
    hi = [max(r[i] for r in rows) for i in range(3)]
    out = []
    for r in rows:
        s = sum(
            w[i] * ((r[i] - lo[i]) / (hi[i] - lo[i]) if hi[i] > lo[i] else 0) for i in range(3)
        )
        out.append(round(100 * (1 - s / total_w), 1))
    return out
