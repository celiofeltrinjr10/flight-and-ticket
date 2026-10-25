"""Gera docs/index.html (o dashboard) a partir de todas as execuções em data/runs/.

Uso: python -m tracker.build_dashboard
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from . import config as config_mod

MADRID = ZoneInfo("Europe/Madrid")
RUNS = config_mod.ROOT / "data" / "runs"
BUSCAS = config_mod.ROOT / "data" / "buscas"
DOCS = config_mod.ROOT / "docs"
PUBLIC = config_mod.ROOT / "data" / "public"   # JSON lido pelo site (Vercel)
WEB_TEMPLATE = config_mod.ROOT / "painel.html"  # cópia do template usada pelo site (Vercel)
TEMPLATE = Path(__file__).with_name("dashboard_template.html")
INDEX_TEMPLATE = Path(__file__).with_name("buscas_template.html")
WEEKDAYS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def eur(v: float, moeda: str) -> str:
    return f"{v:,.0f}".replace(",", ".") + (" €" if moeda == "EUR" else f" {moeda}")


def load_runs(base: Path) -> list[dict]:
    runs = []
    for d in sorted(p for p in base.iterdir() if p.is_dir()) if base.exists() else []:
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
        "lg": int(row["maior_trecho_min"]),
        "src": row["fonte"], "url": row["link"], "hl": classify(row, cfg),
    }


def dashboard_row(row: dict) -> bool:
    """Válida pela configuração, ou descartada só pela regra de horas por voo
    (essa regra é um filtro ajustável no dashboard)."""
    if not row["preco"]:
        return False
    if row["valido"] == "1":
        return True
    return all(m.startswith("trecho ") for m in row["motivo"].split("; "))


def rt_reference(cfg) -> dict[str, dict]:
    """Preços de ida e volta já conferidos, por companhia, na mesma rota (coleta diária e todas as
    buscas dos últimos 7 dias). Servem de referência para estimar a compra conjunta onde ainda não
    houve conferência: a ida e volta de uma companhia fica numa faixa própria, que não acompanha a
    soma dos trechos (ex.: LATAM BCN–SAO entre 1.120 e 1.351 € com somas de 1.669 a 1.921 €)."""
    cutoff = (datetime.now(MADRID).date() - timedelta(days=7)).isoformat()
    main = config_mod.load()
    folders = [RUNS] if (cfg.origem, cfg.destino) == (main.origem, main.destino) else []
    for f in sorted(BUSCAS.iterdir()) if BUSCAS.exists() else []:
        spec = f / "busca.json"
        if spec.exists():
            v = json.loads(spec.read_text(encoding="utf-8"))["viagem"]
            if (v["origem"], v["destino"]) == (cfg.origem, cfg.destino):
                folders.append(f)
    obs: dict[str, list[float]] = defaultdict(list)
    for base in folders:
        for run in load_runs(base):
            if run["dia"] < cutoff:
                continue
            for row in read_csv(run["dir"] / "roundtrip.csv"):
                al = row.get("companhias_ida")
                if row.get("preco_idavolta_mesmos_voos") and al == row.get("companhias_volta"):
                    obs[al].append(float(row["preco_idavolta_mesmos_voos"]))
                if row.get("preco_idavolta_melhor") and al == row.get("companhias_volta_melhor"):
                    obs[al].append(float(row["preco_idavolta_melhor"]))
    return {al: {"med": round(statistics.median(v)), "min": round(min(v)), "max": round(max(v)), "n": len(v)}
            for al, v in obs.items()}


def comparator_groups(options: list[dict], cfg) -> list[dict]:
    """Séries do comparador: destaques com dados; se não houver, as 2 companhias mais presentes."""
    groups = [{"id": h.id, "nome": h.nome, "hl": h.id} for h in cfg.destaques
              if any(o["hl"] == h.id for o in options)]
    if not groups:
        count = defaultdict(set)
        for o in options:
            if "+" not in o["al"]:
                count[o["al"]].add((o["d"], o["date"]))
        names = {o["al"]: o["aln"] for o in options if "+" not in o["al"]}
        for al in sorted(count, key=lambda a: -len(count[a]))[:2]:
            groups.append({"id": al, "nome": names.get(al, al), "al": al})
    return groups


def build(cfg, base: Path, title: str, links: dict) -> dict:
    runs = load_runs(base)
    ok_runs = [r for r in runs if r.get("itinerarios_validos") and not r.get("poc")]
    latest = ok_runs[-1] if ok_runs else None
    last_attempt = runs[-1] if runs else None

    options = []
    roundtrips = []
    errors = []
    if latest:
        options = [option(r, cfg) for r in read_csv(latest["dir"] / "oneway.csv") if dashboard_row(r)]
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

    valid_opts = [o for o in options if o["lg"] <= cfg.max_min_por_trecho]
    return {
        "title": title,
        "links": links,
        "generated_at": datetime.now(MADRID).isoformat(timespec="minutes"),
        "last_attempt": _meta(last_attempt),
        "latest": _meta(latest),
        "config": {
            "moeda": cfg.moeda, "origem": cfg.origem, "destino": cfg.destino,
            "aeroportos_origem": cfg.aeroportos_origem, "aeroportos_destino": cfg.aeroportos_destino,
            "adultos": cfg.adultos, "classe": cfg.classe,
            "ida": [cfg.ida[0].isoformat(), cfg.ida[1].isoformat()],
            "volta": [cfg.volta[0].isoformat(), cfg.volta[1].isoformat()] if cfg.volta else None,
            "deadline": cfg.data_limite_chegada.isoformat() if cfg.data_limite_chegada else None,
            "pesos": cfg.pesos,
            "max_escalas": cfg.max_escalas, "max_horas_trecho": cfg.max_min_por_trecho / 60,
            "destaques": [{"id": h.id, "nome": h.nome} for h in cfg.destaques],
        },
        "options": options,
        "roundtrips": roundtrips,
        "rt_ref": rt_reference(cfg),
        "groups": comparator_groups(options, cfg),
        "errors": [{k: e[k] for k in ("etapa", "direcao", "data", "tentativa", "erro")} for e in errors][-50:],
        "history": {"days": days, "series": dict(series)},
        "insights": insights(valid_opts, roundtrips, series, days, cfg),
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


def write_json(data, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def render(data: dict, out: Path) -> None:
    html = TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html.replace("/*__DATA__*/null", payload), encoding="utf-8")


def best_final(data: dict) -> dict:
    """Preço final da viagem: o menor entre ida e volta conferida e a soma dos dois trechos mais
    baratos (só voos dentro do limite de horas padrão). Viagem só de ida: o trecho mais barato."""
    lim = data["config"]["max_horas_trecho"] * 60
    opts = [o for o in data["options"] if o["lg"] <= lim]
    ida = min((o["p"] for o in opts if o["d"] == "ida"), default=None)
    if not data["config"]["volta"]:
        return {"preco": ida, "tipo": "so_ida"}
    volta = min((o["p"] for o in opts if o["d"] == "volta"), default=None)
    cands = []
    if ida is not None and volta is not None:
        cands.append((ida + volta, "2_passagens"))
    # Só conta ida e volta conferida quando os dois voos estão entre as opções mostradas na página,
    # para a home e a página da viagem mostrarem sempre o mesmo preço.
    shown = {(o["d"], o["date"], o["fl"]) for o in opts}
    for r in data["roundtrips"]:
        for k, ret in (("preco_idavolta_mesmos_voos", r.get("voos_volta")), ("preco_idavolta_melhor", r.get("voos_volta_melhor"))):
            if r.get(k) and ("ida", r["data_ida"], r["voos_ida"]) in shown and ("volta", r["data_volta"], ret) in shown:
                cands.append((float(r[k]), "conferido"))
    if not cands:
        return {"preco": None, "tipo": None}
    preco, tipo = min(cands)
    return {"preco": preco, "tipo": tipo}


def search_title(cfg) -> str:
    t = f"{cfg.origem} → {cfg.destino}" + (f" → {cfg.origem}" if cfg.volta else " (só ida)")
    rng = lambda r: _br(r[0].isoformat()) + ("" if r[0] == r[1] else f"–{_br(r[1].isoformat())}")
    d = f"ida {rng(cfg.ida)}" + (f", volta {rng(cfg.volta)}" if cfg.volta else "")
    return f"{t} · {d}"


def main() -> int:
    cfg = config_mod.load()
    data = build(cfg, RUNS, "Passagens Barcelona ↔ São Paulo", {"buscas": "buscas/"})
    render(data, DOCS / "index.html")
    write_json(data, PUBLIC / "rotas" / "principal.json")
    if WEB_TEMPLATE.parent.exists():
        WEB_TEMPLATE.write_text(TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Dashboard principal: {len(data['options'])} opções, {len(data['history']['days'])} dia(s)")

    entries = []
    for folder in sorted(BUSCAS.iterdir()) if BUSCAS.exists() else []:
        spec = folder / "busca.json"
        if not spec.exists():
            continue
        bcfg = config_mod.from_dict(json.loads(spec.read_text(encoding="utf-8")))
        title = search_title(bcfg)
        bdata = build(bcfg, folder, title, {"principal": "../../", "buscas": "../"})
        render(bdata, DOCS / "buscas" / folder.name / "index.html")
        write_json(bdata, PUBLIC / "buscas" / f"{folder.name}.json")
        latest = bdata["latest"] or bdata["last_attempt"] or {}
        final = best_final(bdata)
        entries.append({
            "slug": folder.name, "title": title, "adultos": bcfg.adultos, "classe": bcfg.classe,
            "moeda": bcfg.moeda, "atualizado": latest.get("fim"), "opcoes": len(bdata["options"]),
            "min": final["preco"], "tipo": final["tipo"], "ok": bool(bdata["latest"]),
            "parcial": (bdata["latest"] or {}).get("etapas") == "A",
        })
        print(f"Busca {folder.name}: {len(bdata['options'])} opções")
    entries.sort(key=lambda e: e["atualizado"] or "", reverse=True)
    idx = INDEX_TEMPLATE.read_text(encoding="utf-8").replace(
        "/*__DATA__*/null", json.dumps(entries, ensure_ascii=False).replace("</", "<\\/"))
    (DOCS / "buscas").mkdir(parents=True, exist_ok=True)
    (DOCS / "buscas" / "index.html").write_text(idx, encoding="utf-8")
    final_main = best_final(data)
    write_json({
        "principal": {"title": data["title"], "atualizado": (data["latest"] or {}).get("fim"),
                      "ida": data["config"]["ida"], "volta": data["config"]["volta"],
                      "min": final_main["preco"], "tipo": final_main["tipo"], "moeda": data["config"]["moeda"]},
        "buscas": entries,
    }, PUBLIC / "index.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
