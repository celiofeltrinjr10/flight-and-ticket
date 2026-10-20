"""Coleta diária de preços.

Uso:
    python -m tracker.collect            # coleta completa (etapas A e B)
    python -m tracker.collect --poc      # prova de conceito: 3 idas + 3 voltas
    python -m tracker.collect --etapa A  # só os trechos de ida

Cada execução grava uma pasta nova em data/runs/AAAA-MM-DD_HHMM/ (nunca
sobrescreve): oneway.csv, roundtrip.csv, errors.csv e meta.json.
"""

from __future__ import annotations

import argparse
import re
import csv
import json
import random
import sys
import time
import traceback
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from . import busca
from . import config as config_mod
from .filters import evaluate, fmt_min
from .gflights import Blocked, NoResults
from .models import CSV_FIELDS, Itinerary, to_row
from .providers import Provider, get_provider
from .scoring import combo_metrics, score

MADRID = ZoneInfo("Europe/Madrid")

RT_FIELDS = [
    "run_id", "consultado_em", "fonte", "data_ida", "data_volta", "destaque", "score_etapa_a",
    "voos_ida", "companhias_ida", "preco_ida", "voos_volta", "companhias_volta", "preco_volta",
    "preco_soma_trechos", "preco_idavolta_mesmos_voos", "voos_volta_melhor",
    "companhias_volta_melhor", "preco_idavolta_melhor", "opcoes_volta_validas", "link", "erro",
]
ERR_FIELDS = ["run_id", "quando", "etapa", "fonte", "direcao", "data", "tentativa", "erro"]


def log(msg: str) -> None:
    print(f"[{datetime.now(MADRID):%H:%M:%S}] {msg}", flush=True)


class Runner:
    def __init__(self, cfg: config_mod.Config, out_dir: Path, run_id: str):
        self.cfg, self.out_dir, self.run_id = cfg, out_dir, run_id
        self.errors: list[dict] = []
        self.searches = self.failures = 0
        self._providers: dict[str, Provider] = {}
        self._last_request = 0.0

    def provider(self, name: str) -> Provider:
        if name not in self._providers:
            self._providers[name] = get_provider(name, self.cfg)
        return self._providers[name]

    def close(self) -> None:
        for p in self._providers.values():
            p.close()

    def _pause(self) -> None:
        lo, hi = self.cfg.pausa
        wait = random.uniform(lo, hi) - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)

    def call(self, etapa: str, provider_name: str, direction: str, day: date, fn):
        """Executa ``fn(provider)`` com pausa, novas tentativas e registro de erro."""
        cfg = self.cfg
        self.searches += 1
        for attempt in range(1, cfg.tentativas + 1):
            self._pause()
            try:
                provider = self.provider(provider_name)
                return fn(provider)
            except Exception as e:  # nunca derruba a execução inteira
                msg = f"{type(e).__name__}: {e}"
                self.errors.append({
                    "run_id": self.run_id, "quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "etapa": etapa, "fonte": provider_name, "direcao": direction,
                    "data": day.isoformat(), "tentativa": attempt, "erro": msg[:500],
                })
                log(f"  ! {etapa} {direction} {day} tentativa {attempt}/{cfg.tentativas}: {msg[:160]}")
                if "não definida" in msg or "não implementada" in msg or isinstance(e, NoResults):
                    break  # repetir não adianta (configuração ou combinação sem resultado)
                if attempt < cfg.tentativas:
                    wait = cfg.espera_base_s * 3 ** (attempt - 1) * (2 if isinstance(e, Blocked) else 1)
                    time.sleep(wait + random.uniform(0, 3))
            finally:
                self._last_request = time.monotonic()
        self.failures += 1
        return None

    # --- Etapa A ---------------------------------------------------------------
    def stage_a(self, days: dict[str, list[date]]) -> list[Itinerary]:
        cfg = self.cfg
        results: list[Itinerary] = []
        consecutive = 0
        tasks = [(d, day) for d in ("ida", "volta") for day in days.get(d, [])]
        log(f"Etapa A: {len(tasks)} buscas só de ida (fonte {cfg.fonte_a})")
        for i, (direction, day) in enumerate(tasks, 1):
            its = self.call("A", cfg.fonte_a, direction, day,
                            lambda p: p.search_oneway(direction, day))
            if its is None and cfg.fonte_a_reserva:
                log(f"  tentando a fonte reserva {cfg.fonte_a_reserva}")
                its = self.call("A", cfg.fonte_a_reserva, direction, day,
                                lambda p: p.search_oneway(direction, day))
                if its is not None:
                    self.failures -= 1  # a reserva salvou esta data
            if its is None:
                consecutive += 1
                if consecutive >= cfg.max_falhas_seguidas:
                    log(f"Etapa A interrompida: {consecutive} falhas seguidas (provável bloqueio)")
                    break
                continue
            consecutive = 0
            for it in its:
                evaluate(it, cfg)
            ok = [it for it in its if it.valid]
            best = min((it.price for it in ok), default=None)
            log(f"  [{i}/{len(tasks)}] {direction} {day}: {len(its)} opções, {len(ok)} válidas"
                + (f", mín. {best:.0f} {cfg.moeda}" if best else ""))
            results.extend(its)
        return results

    # --- Etapa B ---------------------------------------------------------------
    def pick_combos(self, its: list[Itinerary]) -> list[tuple[float, Itinerary, Itinerary]]:
        cfg = self.cfg
        per_day: dict[tuple[str, date], list[Itinerary]] = {}
        for it in its:
            if it.valid:
                per_day.setdefault((it.direction, it.date), []).append(it)
        cands = {"ida": [], "volta": []}
        for (direction, _), lst in per_day.items():
            lst.sort(key=lambda x: x.price)
            chosen = {x.flights: x for x in lst[:3]}
            for h in cfg.destaques:  # garante o melhor de cada destaque no dia
                hx = next((x for x in lst if cfg.destaque(x) is h), None)
                if hx:
                    chosen.setdefault(hx.flights, hx)
            cands[direction].extend(chosen.values())
        combos = [(o, r) for o in cands["ida"] for r in cands["volta"]
                  if not cfg.somente_mesma_cia or o.airlines == r.airlines]
        if not combos:
            return []
        scores = score([combo_metrics(o, r) for o, r in combos], cfg.pesos)
        ranked = sorted(zip(scores, combos), key=lambda x: -x[0])

        picked, used, per_out, per_ret, per_pair = [], set(), {}, {}, {}

        def take(sc, o, r) -> bool:
            key, pair = (o.date, o.flights, r.date), (o.flights, r.flights)
            if key in used or per_out.get(o.date, 0) >= cfg.max_por_data \
                    or per_ret.get(r.date, 0) >= cfg.max_por_data \
                    or per_pair.get(pair, 0) >= cfg.max_por_par_de_voos:
                return False
            used.add(key)
            per_out[o.date] = per_out.get(o.date, 0) + 1
            per_ret[r.date] = per_ret.get(r.date, 0) + 1
            per_pair[pair] = per_pair.get(pair, 0) + 1
            picked.append((sc, o, r))
            return True

        for h in cfg.destaques:
            n = 0
            for sc, (o, r) in ranked:
                if n >= cfg.vagas_por_destaque:
                    break
                if cfg.destaque(o) is h and cfg.destaque(r) is h and take(sc, o, r):
                    n += 1
        for sc, (o, r) in ranked:
            if len(picked) >= cfg.combinacoes:
                break
            take(sc, o, r)
        return picked

    def stage_b(self, its: list[Itinerary]) -> list[dict]:
        cfg = self.cfg
        combos = self.pick_combos(its)
        log(f"Etapa B: {len(combos)} combinações de ida e volta (fonte {cfg.fonte_b})")
        rows = []
        for i, (sc, out, ret) in enumerate(combos, 1):
            h = cfg.destaque(out) if cfg.destaque(out) is cfg.destaque(ret) else None
            row = {
                "run_id": self.run_id, "consultado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "fonte": cfg.fonte_b, "data_ida": out.date.isoformat(), "data_volta": ret.date.isoformat(),
                "destaque": h.id if h else "", "score_etapa_a": sc,
                "voos_ida": out.flights, "companhias_ida": "+".join(out.airlines), "preco_ida": f"{out.price:.0f}",
                "voos_volta": ret.flights, "companhias_volta": "+".join(ret.airlines), "preco_volta": f"{ret.price:.0f}",
                "preco_soma_trechos": f"{out.price + ret.price:.0f}",
                "preco_idavolta_mesmos_voos": "", "voos_volta_melhor": "", "companhias_volta_melhor": "",
                "preco_idavolta_melhor": "", "opcoes_volta_validas": 0, "link": "", "erro": "",
            }
            quotes = self.call("B", cfg.fonte_b, "idavolta", out.date,
                               lambda p: p.search_roundtrip(out, ret.date))
            if quotes is None:
                row["erro"] = "falhou (ver errors.csv)"
            else:
                valid = [q for q in quotes if evaluate(q.ret, cfg).valid]
                same = next((q for q in valid if q.ret.flights == ret.flights), None)
                best = min(valid, key=lambda q: q.total_price, default=None)
                row["opcoes_volta_validas"] = len(valid)
                if same:
                    row["preco_idavolta_mesmos_voos"] = f"{same.total_price:.0f}"
                if best:
                    row.update(voos_volta_melhor=best.ret.flights,
                               companhias_volta_melhor="+".join(best.ret.airlines),
                               preco_idavolta_melhor=f"{best.total_price:.0f}", link=best.link)
                elif quotes:
                    row["link"] = quotes[0].link
                if not valid:
                    row["erro"] = "nenhuma volta válida na resposta"
            log(f"  [{i}/{len(combos)}] {out.date} {out.flights} + {ret.date}: soma {row['preco_soma_trechos']}, "
                f"ida e volta mesmos voos {row['preco_idavolta_mesmos_voos'] or '-'}, "
                f"melhor ida e volta {row['preco_idavolta_melhor'] or '-'} {row['voos_volta_melhor']}")
            rows.append(row)
        return rows


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def last_partial_run(base: Path) -> Path | None:
    """Última execução que parou depois da etapa A (para a etapa B continuar)."""
    for d in sorted((p for p in base.iterdir() if p.is_dir()), reverse=True) if base.exists() else []:
        meta = d / "meta.json"
        if meta.exists() and (d / "itinerarios.json").exists():
            if json.loads(meta.read_text(encoding="utf-8")).get("etapas") == "A":
                return d
            return None
    return None


def save_itineraries(its: list[Itinerary], path: Path) -> None:
    path.write_text(json.dumps([it.to_dict() for it in its], ensure_ascii=False), encoding="utf-8")


def load_itineraries(path: Path) -> list[Itinerary]:
    return [Itinerary.from_dict(d) for d in json.loads(path.read_text(encoding="utf-8"))]


def read_errors(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def new_run_dir(base: Path) -> tuple[str, Path]:
    run_id = datetime.now(MADRID).strftime("%Y-%m-%d_%H%M")
    path, n = base / run_id, 1
    while path.exists():
        n += 1
        path = base / f"{run_id}_{n}"
    path.mkdir(parents=True)
    return path.name, path


def print_poc(its: list[Itinerary], rt_rows: list[dict], cfg) -> None:
    print("\n=== DADOS BRUTOS: trechos só de ida ===")
    for it in sorted(its, key=lambda x: (x.direction, x.date, x.price or 1e9)):
        segs = "  ".join(f"{s.flight} {s.origin}-{s.dest} {s.departure:%d/%m %H:%M}->{s.arrival:%d/%m %H:%M} "
                         f"({fmt_min(s.duration_min)})" for s in it.segments)
        conn = ",".join(fmt_min(x) for x in it.layovers_min) or "-"
        flag = "OK " if it.valid else "DESCARTADO"
        print(f"{flag:10} {it.direction:5} {it.date} {it.price or 0:>6.0f} {cfg.moeda} "
              f"{'+'.join(it.airlines):8} escalas={it.stops} total={fmt_min(it.total_min)} conexão={conn}")
        print(f"{'':10} {segs}")
        if not it.valid:
            print(f"{'':10} motivo: {it.reason}")
    print("\n=== IDA E VOLTA (etapa B) ===")
    for r in rt_rows:
        print(f"{r['data_ida']} {r['voos_ida']:16} + {r['data_volta']} {r['voos_volta']:16} "
              f"soma={r['preco_soma_trechos']:>5}  mesmos voos={r['preco_idavolta_mesmos_voos'] or '-':>5}  "
              f"melhor={r['preco_idavolta_melhor'] or '-':>5} ({r['voos_volta_melhor']}) {r['erro']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--poc", action="store_true", help="prova de conceito com poucas datas")
    ap.add_argument("--etapa", choices=["A", "B", "AB"], default="AB",
                    help="A = só trechos de ida; B = continua a última execução que parou na etapa A")
    ap.add_argument("--config", default=None)
    g = ap.add_argument_group("busca sob demanda (grava em data/buscas/)")
    g.add_argument("--busca", action="store_true", help="busca avulsa com os parâmetros abaixo")
    g.add_argument("--origem", help="código IATA de aeroporto ou cidade (ex. BCN, LON, SAO)")
    g.add_argument("--destino")
    g.add_argument("--ida", help="AAAA-MM-DD ou AAAA-MM-DD a AAAA-MM-DD")
    g.add_argument("--volta", default="", help="igual à ida; vazio = só ida")
    g.add_argument("--adultos", type=int)
    g.add_argument("--classe")
    g.add_argument("--max-escalas", type=int)
    g.add_argument("--moeda")
    g.add_argument("--data-limite", default="", help="data-limite de chegada da ida (opcional)")
    g.add_argument("--slug", default="", help="identificador da busca (o site manda o seu)")
    args = ap.parse_args(argv)

    today = datetime.now(MADRID).date()
    if args.busca:
        try:
            raw, slug = busca.build_raw(config_mod.load(args.config).raw, args)
            if args.slug:
                if not re.fullmatch(r"[A-Za-z0-9_-]{3,120}", args.slug):
                    raise ValueError("slug inválido")
                slug = args.slug
        except ValueError as e:
            log(f"ERRO no formulário: {e}")
            return 2
        cfg = config_mod.from_dict(raw)
        base = config_mod.ROOT / "data" / "buscas" / slug
        base.mkdir(parents=True, exist_ok=True)
        (base / "busca.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2, default=str),
                                         encoding="utf-8")
        days = {d: cfg.dias(d) for d in cfg.direcoes}
        n = sum(len(v) for v in days.values())
        if n > busca.MAX_DIAS:
            log(f"ERRO: {n} datas pedidas; o máximo por busca é {busca.MAX_DIAS}. Encurte os intervalos.")
            return 2
    elif args.poc:
        cfg = config_mod.load(args.config)
        cfg.filtro_no_servidor = False
        days = {"ida": cfg.poc_ida, "volta": cfg.poc_volta}
        cfg.combinacoes, cfg.vagas_por_destaque, cfg.max_por_data = 4, 1, 2
        base = config_mod.ROOT / "data" / "poc"
    else:
        cfg = config_mod.load(args.config)
        days = {d: cfg.dias(d) for d in cfg.direcoes}
        base = config_mod.ROOT / "data" / "runs"
    days = {d: [x for x in v if x >= today] for d, v in days.items()}

    if args.etapa == "B":
        out_dir = last_partial_run(base)
        if out_dir is None:
            log("ERRO: não há execução parada na etapa A para continuar.")
            return 2
        run_id = out_dir.name
        meta_prev = json.loads((out_dir / "meta.json").read_text(encoding="utf-8"))
        started = datetime.fromisoformat(meta_prev["inicio"])
    else:
        run_id, out_dir = new_run_dir(base)
        started = datetime.now(timezone.utc)
        meta_prev = {}
    log(f"Execução {run_id} -> {out_dir} (etapa {args.etapa})")
    runner = Runner(cfg, out_dir, run_id)
    its: list[Itinerary] = []
    rt_rows: list[dict] = []
    fatal = ""
    try:
        if args.etapa == "B":
            its = load_itineraries(out_dir / "itinerarios.json")
            runner.searches = meta_prev.get("buscas", 0)
            runner.failures = meta_prev.get("falhas", 0)
            runner.errors = read_errors(out_dir / "errors.csv")
        else:
            its = runner.stage_a(days)
            write_csv(out_dir / "oneway.csv", CSV_FIELDS, [to_row(it, run_id) for it in its])
            save_itineraries(its, out_dir / "itinerarios.json")
        if "B" in args.etapa and cfg.volta:
            rt_rows = runner.stage_b(its)
            write_csv(out_dir / "roundtrip.csv", RT_FIELDS, rt_rows)
    except Exception:
        fatal = traceback.format_exc()
        log("ERRO inesperado:\n" + fatal)
    finally:
        runner.close()
        write_csv(out_dir / "errors.csv", ERR_FIELDS, runner.errors)
        etapas = "A" if args.etapa == "A" and cfg.volta else "AB"
        meta = {
            "run_id": run_id, "inicio": started.isoformat(timespec="seconds"),
            "fim": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "poc": args.poc, "etapas": etapas,
            "fontes": {"etapa_a": cfg.fonte_a, "etapa_a_reserva": cfg.fonte_a_reserva, "etapa_b": cfg.fonte_b},
            "buscas": runner.searches, "falhas": runner.failures, "tentativas_com_erro": len(runner.errors),
            "itinerarios": len(its), "itinerarios_validos": sum(it.valid for it in its),
            "combinacoes_ida_volta": len(rt_rows), "erro_fatal": fatal[-2000:],
        }
        (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.poc:
        print_poc(its, rt_rows, cfg)
    log(f"Fim: {runner.searches} buscas, {runner.failures} falhas, {len(its)} itinerários "
        f"({meta['itinerarios_validos']} válidos), {len(rt_rows)} combinações")
    # Só falha (código 1) se nada foi coletado — falhas parciais não param a automação.
    return 1 if fatal or not its else 0


if __name__ == "__main__":
    sys.exit(main())
