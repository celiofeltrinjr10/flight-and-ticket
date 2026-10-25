"""Leitura das páginas do Google Flights (compartilhado pelas fontes "google_*").

O Google embute os resultados da busca num bloco JavaScript chamado ``ds:1``.
As posições usadas abaixo foram mapeadas a partir de respostas reais
(outubro/2026) e podem mudar sem aviso: se o Google alterar a página, é aqui
que o conserto acontece.
"""

from __future__ import annotations

import base64
import json
import re
from datetime import date, datetime
from typing import Any, Sequence

from .models import Itinerary, Segment

SEARCH_URL = "https://www.google.com/travel/flights/search"
# Resposta "Rejeitar tudo" ao aviso de cookies da UE (só cookies essenciais).
CONSENT_COOKIE_NAME = "SOCS"
CONSENT_COOKIE_VALUE = "CAESHAgBEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmVuIAEaBgiAo_CmBg"


class PageError(Exception):
    """A página veio, mas sem os dados esperados."""


class EmptyResult(PageError):
    """O Google respondeu "nenhum voo" para uma busca só de ida. Numa rota servida todo dia isso quase
    sempre é limitação temporária do Google, não falta de voos: tenta de novo e usa a fonte reserva."""


class NoResults(PageError):
    """A página carregou, mas o Google não trouxe opções (ex.: ida e volta não vendida junto)."""


class Blocked(PageError):
    """O Google pediu verificação (tráfego incomum / CAPTCHA) ou limitou as requisições."""


_DS1_SCRIPT = re.compile(r'<script[^>]*class="ds:1"[^>]*>(.*?)</script>', re.S)


def page_payload(html: str) -> list | None:
    """Devolve o bloco ``ds:1`` da página. ``None`` = busca sem nenhum voo."""
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    title = title.group(1) if title else ""
    if "Before you continue" in title or "consent.google" in html[:5000]:
        raise PageError("o Google mostrou a tela de consentimento de cookies")
    if "unusual traffic" in html or "/sorry/" in html[:5000]:
        raise Blocked("o Google pediu verificação de tráfego incomum (bloqueio)")
    m = _DS1_SCRIPT.search(html)
    if not m or "data:" not in m.group(1):
        raise PageError(f"página sem o bloco de resultados (título: {title[:80]!r})")
    js = m.group(1)
    if "errorHasStatus: true" in js:
        return None
    return json.loads(js.split("data:", 1)[1].rsplit(", sideChannel", 1)[0])


def rpc_payloads(text: str) -> list[list]:
    """Blocos de resultado de uma resposta GetShoppingResults (formato ``wrb.fr``)."""
    out = []
    for line in text.splitlines():
        if '"wrb.fr"' not in line:
            continue
        try:
            chunks = json.loads(line)
        except ValueError:
            continue
        for ch in chunks:
            if isinstance(ch, list) and len(ch) > 2 and ch[0] == "wrb.fr" and ch[2]:
                out.append(json.loads(ch[2]))
    return out


def raw_rows(payload: list | None) -> list:
    """Linhas de itinerário dos dois blocos ("melhores" [2] e "outros" [3])."""
    if not payload:
        return []
    rows = []
    for idx in (2, 3):
        block = payload[idx] if len(payload) > idx else None
        if isinstance(block, list) and block and isinstance(block[0], list):
            rows.extend(block[0])
    return rows


def _time(v: list | None) -> tuple[int, int]:
    # O Google omite componentes zero: [8] = 08:00, [None, 31] = 00:31.
    p = [*(v or []), None, None]
    return p[0] or 0, p[1] or 0


def _dt(d: list, t: list | None) -> datetime:
    return datetime(*d[:3], *_time(t))


def row_to_itinerary(
    row: list, *, direction: str, day: date, source: str, queried_at: datetime,
    currency: str, link: str,
) -> Itinerary:
    it = row[0]
    price = None
    try:
        price = float(row[1][0][1])
    except (TypeError, IndexError):
        pass
    segments = []
    for s in it[2]:
        flight = s[22] or [None, None, None, None]
        segments.append(Segment(
            origin=s[3], dest=s[6],
            departure=_dt(s[20], s[8]), arrival=_dt(s[21], s[10]),
            duration_min=int(s[11]),
            airline=flight[0] or "", number=str(flight[1] or ""),
            airline_name=flight[3] or "", aircraft=s[17] or "",
        ))
    layovers = []
    if isinstance(it[13], list) and it[13]:
        layovers = [int(x[0]) for x in it[13]]
    else:  # mesma cidade -> mesmo fuso, então a diferença de hora local vale
        layovers = [int((b.departure - a.arrival).total_seconds() // 60)
                    for a, b in zip(segments, segments[1:])]
    total = int(it[9]) if it[9] else sum(s.duration_min for s in segments) + sum(layovers)
    return Itinerary(
        direction=direction, date=day, segments=segments, layovers_min=layovers,
        total_min=total, price=price, currency=currency, source=source,
        queried_at=queried_at, link=link, airline_names=list(it[1] or []),
    )


# --- Montagem da consulta (parâmetro ``tfs``) --------------------------------
# Protobuf da URL do Google Flights. O fast-flights 3.1.0 não tem o campo de
# "voo selecionado" (3.4), necessário para pedir as voltas de uma ida escolhida,
# então a fonte de ida e volta usa este codificador. Layout conforme o projeto
# fli (github.com/punitarani/fli, licença MIT), conferido em out/2026.

def _varint(n: int) -> bytes:
    out = bytearray()
    while True:
        b, n = n & 0x7F, n >> 7
        out.append(b | 0x80 if n else b)
        if not n:
            return bytes(out)


def _ld(field: int, data: bytes | str) -> bytes:
    data = data.encode() if isinstance(data, str) else data
    return _varint(field << 3 | 2) + _varint(len(data)) + data


def _vi(field: int, value: int) -> bytes:
    return _varint(field << 3) + _varint(value)


def encode_leg(day: date, origins: Sequence[str], dests: Sequence[str],
               max_stops: int | None, selected: Sequence[Segment] = ()) -> bytes:
    body = _ld(2, day.isoformat())
    if max_stops is not None:
        body += _vi(5, max_stops)
    for s in selected:
        body += _ld(4, _ld(1, s.origin) + _ld(2, s.departure.date().isoformat())
                    + _ld(3, s.dest) + _ld(5, s.airline) + _ld(6, s.number))
    for code in origins:
        body += _ld(13, _vi(1, 1) + _ld(2, code))
    for code in dests:
        body += _ld(14, _vi(1, 1) + _ld(2, code))
    return _ld(3, body)


def encode_tfs(legs: Sequence[bytes], *, one_way: bool, adults: int, seat: int) -> str:
    payload = _vi(1, 28) + _vi(2, 2) + b"".join(legs)
    payload += b"".join(_vi(8, 1) for _ in range(adults))
    payload += _vi(9, seat) + _vi(14, 1) + _vi(19, 2 if one_way else 1)
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def search_url(tfs: str, currency: str, language: str = "en") -> str:
    return f"{SEARCH_URL}?tfs={tfs}&hl={language}&curr={currency}"


def debug_shape(payload: Any) -> str:
    """Resumo curto da estrutura (para mensagens de erro quando o Google muda)."""
    try:
        return str([(i, type(x).__name__) for i, x in enumerate(payload)][:8])
    except TypeError:
        return type(payload).__name__
