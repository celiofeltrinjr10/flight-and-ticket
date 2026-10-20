"""Busca sob demanda: monta a configuração a partir do formulário do GitHub Actions.

Cada busca vira uma pasta data/buscas/<identificador>/ com busca.json (os
parâmetros) e uma subpasta por execução. Repetir a mesma busca acumula
histórico na mesma pasta, como a coleta diária.
"""

from __future__ import annotations

import copy
import re
from datetime import date

from .config import SEAT_CODES

MAX_DIAS = 150  # datas de ida + volta por busca (~6 s cada)
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_IATA = re.compile(r"^[A-Z]{3}$")


def parse_range(text: str, campo: str) -> tuple[date, date] | None:
    """'2026-11-01', '2026-11-01 a 2026-11-10' ou '2026-11-01..2026-11-10'."""
    found = _DATE.findall(text or "")
    if not found:
        if (text or "").strip():
            raise ValueError(f"{campo}: use o formato AAAA-MM-DD ou AAAA-MM-DD a AAAA-MM-DD")
        return None
    ini, fim = date.fromisoformat(found[0]), date.fromisoformat(found[-1])
    if fim < ini:
        raise ValueError(f"{campo}: a data final vem antes da inicial")
    return ini, fim


def build_raw(main_raw: dict, args) -> tuple[dict, str]:
    raw = copy.deepcopy(main_raw)
    v = raw["viagem"]
    origem = (args.origem or "").strip().upper()
    destino = (args.destino or "").strip().upper()
    for nome, code in (("origem", origem), ("destino", destino)):
        if not _IATA.match(code):
            raise ValueError(f"{nome}: use um código de 3 letras (ex. BCN, LON, SAO)")
    ida = parse_range(args.ida, "ida")
    if not ida:
        raise ValueError("ida: informe ao menos uma data")
    volta = parse_range(args.volta, "volta")
    if volta and volta[0] < ida[0]:
        raise ValueError("volta: começa antes da ida")
    same_route = (origem, destino) == (v["origem"], v["destino"])

    v.update(
        origem=origem, destino=destino,
        # Aeroportos aceitos: os da configuração principal se a rota for a mesma;
        # senão, qualquer aeroporto que o Google devolver para os códigos pedidos.
        aeroportos_origem=v.get("aeroportos_origem") if same_route else [],
        aeroportos_destino=v.get("aeroportos_destino") if same_route else [],
        ida={"inicio": ida[0].isoformat(), "fim": ida[1].isoformat()},
        volta={"inicio": volta[0].isoformat(), "fim": volta[1].isoformat()} if volta else None,
        data_limite_chegada=parse_range(args.data_limite, "data-limite")[0].isoformat()
        if (args.data_limite or "").strip() else None,
    )
    if args.adultos:
        v["adultos"] = int(args.adultos)
    if args.classe:
        if args.classe not in SEAT_CODES:
            raise ValueError(f"classe: use {', '.join(SEAT_CODES)}")
        v["classe"] = args.classe
    if args.moeda:
        v["moeda"] = args.moeda.strip().upper()
    if args.max_escalas is not None:
        raw["filtros"]["max_escalas"] = int(args.max_escalas)
    if not same_route:
        raw["destaques"] = []
    raw["etapa_b"].update(combinacoes=20, vagas_por_destaque=2 if same_route else 0)
    raw.pop("prova_de_conceito", None)

    slug = f"{origem}-{destino}_{ida[0]:%Y%m%d}-{ida[1]:%Y%m%d}"
    if volta:
        slug += f"_volta-{volta[0]:%Y%m%d}-{volta[1]:%Y%m%d}"
    if v["adultos"] != 1:
        slug += f"_{v['adultos']}adultos"
    if v["classe"] != "economy":
        slug += f"_{v['classe']}"
    return raw, slug
