"""Gera docs/index.html (o dashboard) a partir de todas as execuções em data/runs/.

Uso: python -m tracker.build_dashboard
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from . import config as config_mod

MADRID = ZoneInfo("Europe/Madrid")
RUNS = config_mod.ROOT / "data" / "runs"
TEMPLATE = Path(__file__).with_name("dashboard_template.html")
OUT = config_mod.ROOT / "docs" / "index.html"
WEEKDAYS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def eur(v: float, moeda: str) -> str:
    return f"{v:,.0f}".replace(",", ".") + (" €" if moeda == "EUR" else f" {moeda}")


def load_runs() -> list[dict]:
    runs = []
    for d in sorted(p for p in RUNS.iterdir() if p.is_dir()) if RUNS.exists() else []:
        meta_path = d / "meta.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["dir"] = d
        meta["dia"] = d.name[:10]
        runs.append(meta)
    return runs


def classify(row: dict, cfg) -> str:
    stops = int(row["escalas"])
    obj = SimpleNamespace(
        airlines=row["companhias"].split("+"), stops=stops,
        connection_airports=row["rota"].split("-")[1:-1],
    )
    h = cfg.destaque(obj)
    return h.id if h else ""


def option(row: dict, cfg) -> dict:
    return {
        "d": row["direcao"], "date": row["data"], "p": float(row["preco"]),
        "al": row["companhias"], "aln": row["companhias_nomes"], "fl": row["voos"],
        "rt": row["rota"], "st": int(row["escalas"]),
        "seg": [int(x) for x in row["trechos_min"].split("|") if x],
        "cn": [int(x) for x in row["conexoes_min"].split("|") if x],
        "tot": int(row["duracao_total_min"]), "dep": row["partida"], "arr": row["chegada"],
        "src": row["fonte"], "url": row["link"], "hl": classify(row, cfg),
    }


def build(cfg) -> dict:
    runs = load_runs()
    ok_runs = [r for r in runs if r.get("itinerarios_validos") and not r.get("poc")]
    latest = ok_runs[-1] if ok_runs else None
    last_attempt = runs[-1] if runs else None

    options = []
    roundtrips = []
    errors = []
    if latest:
        options = [option(r, cfg) for r in read_csv(latest["dir"] / "oneway.csv")
                   if r["valido"] == "1" and r["preco"]]
        roundtrips = read_csv(latest["dir"] / "roundtrip.csv")
    if last_attempt:
        errors = read_csv(last_attempt["dir"] / "errors.csv")

    # Histórico: última execução bem-sucedida de cada dia.
    by_day: dict[str, dict] = {}
    for r in ok_runs:
        by_day[r["dia"]] = r
    days = sorted(by_day)
    series: dict[str, list] = defaultdict(lambda: [None] * len(days))
    for i, day in enumerate(days):
        mins: dict[str, float] = {}
        for row in read_csv(by_day[day]["dir"] / "oneway.csv"):
            if row["valido"] != "1" or not row["preco"]:
                continue
            p = float(row["preco"])
            cat = classify(row, cfg) or "outra"
            for key in (f"{row['direcao']}|{row['data']}|all", f"{row['direcao']}|{row['data']}|{cat}"):
                mins[key] = min(p, mins.get(key, p))
        for k, v in mins.items():
            series[k][i] = v

    return {
        "generated_at": datetime.now(MADRID).isoformat(timespec="minutes"),
        "last_attempt": _meta(last_attempt),
        "latest": _meta(latest),
        "config": {
            "moeda": cfg.moeda, "origem": cfg.origem, "destino": cfg.destino,
            "aeroportos_destino": cfg.aeroportos_destino,
            "ida": [cfg.ida[0].isoformat(), cfg.ida[1].isoformat()],
            "volta": [cfg.volta[0].isoformat(), cfg.volta[1].isoformat()],
            "deadline": cfg.data_limite_chegada.isoformat(), "pesos": cfg.pesos,
            "max_escalas": cfg.max_escalas, "max_horas_trecho": cfg.max_min_por_trecho / 60,
            "destaques": [{"id": h.id, "nome": h.nome} for h in cfg.destaques],
        },
        "options": options,
        "roundtrips": roundtrips,
        "errors": [{k: e[k] for k in ("etapa", "direcao", "data", "tentativa", "erro")} for e in errors][-50:],
        "history": {"days": days, "series": dict(series)},
        "insights": insights(options, roundtrips, series, days, cfg),
    }


def _meta(r: dict | None) -> dict | None:
    if not r:
        return None
    return {k: (str(v) if isinstance(v, Path) else v) for k, v in r.items() if k != "dir"}


def insights(options, roundtrips, series, days, cfg) -> list[str]:
    out = []
    m = cfg.moeda
    daymin: dict[tuple[str, str], float] = {}
    for o in options:
        k = (o["d"], o["date"])
        daymin[k] = min(o["p"], daymin.get(k, o["p"]))
    for direction in ("ida", "volta"):
        by_wd = defaultdict(list)
        for (d, dt), p in daymin.items():
            if d == direction:
                by_wd[date.fromisoformat(dt).weekday()].append(p)
        if len(by_wd) >= 3:
            avg = {wd: statistics.mean(v) for wd, v in by_wd.items()}
            lo, hi = min(avg, key=avg.get), max(avg, key=avg.get)
            out.append(f"{direction.capitalize()}: {WEEKDAYS[lo]} é o dia da semana mais barato "
                       f"(média {eur(avg[lo], m)}); {WEEKDAYS[hi]} o mais caro ({eur(avg[hi], m)}).")

    if len(days) >= 2:
        drops, rises = [], []
        for key, vals in series.items():
            d, dt, cat = key.split("|")
            if cat != "all":
                continue
            now, prev = vals[-1], vals[-2]
            if now and prev:
                ch = now / prev - 1
                if ch <= -0.10:
                    drops.append((ch, d, dt, prev, now))
                elif ch >= 0.10:
                    rises.append((ch, d, dt, prev, now))
        if drops:
            drops.sort()
            txt = ", ".join(f"{d} {_br(dt)} ({eur(a, m)} → {eur(b, m)})" for _, d, dt, a, b in drops[:5])
            out.append(f"{len(drops)} data(s) caíram mais de 10% desde a coleta anterior: {txt}.")
        if rises:
            rises.sort(reverse=True)
            txt = ", ".join(f"{d} {_br(dt)} ({eur(a, m)} → {eur(b, m)})" for _, d, dt, a, b in rises[:5])
            out.append(f"{len(rises)} data(s) subiram mais de 10%: {txt}.")
        if not drops and not rises:
            out.append("Nenhuma data variou mais de 10% desde a coleta anterior.")
    else:
        out.append("Tendências aparecem a partir da segunda coleta diária.")

    ids = [h.id for h in cfg.destaques[:2]]
    if len(ids) == 2:
        a, b = ids
        names = {h.id: h.nome for h in cfg.destaques}
        for direction in ("ida", "volta"):
            best = defaultdict(dict)
            for o in options:
                if o["d"] == direction and o["hl"] in ids:
                    cur = best[o["date"]].get(o["hl"])
                    best[o["date"]][o["hl"]] = min(o["p"], cur) if cur else o["p"]
            diffs = [v[a] - v[b] for v in best.values() if a in v and b in v]
            if diffs:
                avg = statistics.mean(diffs)
                cheaper, dearer = (names[b], names[a]) if avg > 0 else (names[a], names[b])
                out.append(f"{direction.capitalize()}: {cheaper} sai em média {eur(abs(avg), m)} mais barata que "
                           f"{dearer} ({len(diffs)} datas com as duas).")

    same = [(float(r["preco_soma_trechos"]), float(r["preco_idavolta_mesmos_voos"]))
            for r in roundtrips if r.get("preco_idavolta_mesmos_voos")]
    if same:
        sav = statistics.mean(s - rt for s, rt in same)
        word = "mais barata" if sav > 0 else "mais cara"
        out.append(f"Comprando ida e volta juntas (mesmos voos), a passagem sai em média {eur(abs(sav), m)} "
                   f"{word} que dois trechos separados ({len(same)} combinações conferidas).")
    mixed = [r for r in roundtrips if not r.get("preco_idavolta_mesmos_voos") and r.get("preco_idavolta_melhor")]
    if mixed:
        out.append(f"Em {len(mixed)} combinação(ões) o Google não vende a mesma volta numa passagem única de ida e "
                   "volta (em geral, companhias diferentes): compare a soma dos trechos com a melhor ida e volta "
                   "encontrada para aquela ida.")
    return out


def _br(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day:02d}/{d.month:02d}"


def main() -> int:
    cfg = config_mod.load()
    data = build(cfg)
    html = TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = html.replace("/*__DATA__*/null", payload)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    (OUT.parent / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Dashboard gerado: {OUT} ({len(data['options'])} opções, "
          f"{len(data['history']['days'])} dia(s) de histórico)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
