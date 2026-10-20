"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { LUGARES, MAX_DATAS } from "@/lib/busca";

const addDays = (d: Date, n: number) => new Date(d.getTime() + n * 864e5).toISOString().slice(0, 10);

export default function SearchForm() {
  const router = useRouter();
  const today = new Date();
  const [f, setF] = useState({
    origem: "BCN", destino: "SAO",
    idaInicio: addDays(today, 21), idaFim: addDays(today, 35),
    voltaInicio: addDays(today, 49), voltaFim: addDays(today, 63),
    adultos: "1", convite: "",
  });
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    try {
      const c = localStorage.getItem("convite");
      if (c) setF((x) => ({ ...x, convite: c }));
    } catch {}
  }, []);

  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setF((x) => ({ ...x, [k]: e.target.value }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErro("");
    setEnviando(true);
    try {
      const res = await fetch("/api/busca", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...f, adultos: Number(f.adultos) }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.erro || "Algo deu errado. Tente de novo.");
      try { localStorage.setItem("convite", f.convite); } catch {}
      const n = Math.round((Date.parse(f.idaFim) - Date.parse(f.idaInicio)) / 864e5) + 1 +
        (f.voltaInicio && f.voltaFim ? Math.round((Date.parse(f.voltaFim) - Date.parse(f.voltaInicio)) / 864e5) + 1 : 0);
      router.push(`/busca/${body.slug}?desde=${encodeURIComponent(body.desde)}&datas=${n}`);
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Algo deu errado. Tente de novo.");
      setEnviando(false);
    }
  }

  const lugar = (k: "origem" | "destino") => (
    <select id={k} value={f[k]} onChange={set(k)}>
      {LUGARES.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
    </select>
  );

  return (
    <form className="search" onSubmit={submit}>
      <div className="row2">
        <label className="field"><span>De</span>{lugar("origem")}</label>
        <label className="field"><span>Para</span>{lugar("destino")}</label>
      </div>
      <div className="field">
        <span>Ida entre</span>
        <div className="dates">
          <input id="idaInicio" type="date" value={f.idaInicio} onChange={set("idaInicio")} aria-label="Ida a partir de" required />
          <i>e</i>
          <input id="idaFim" type="date" value={f.idaFim} onChange={set("idaFim")} aria-label="Ida até" required />
        </div>
      </div>
      <div className="field">
        <span>Volta entre (opcional)</span>
        <div className="dates">
          <input id="voltaInicio" type="date" value={f.voltaInicio} onChange={set("voltaInicio")} aria-label="Volta a partir de" />
          <i>e</i>
          <input id="voltaFim" type="date" value={f.voltaFim} onChange={set("voltaFim")} aria-label="Volta até" />
        </div>
      </div>
      <label className="field" style={{ maxWidth: 160 }}>
        <span>Adultos</span>
        <select id="adultos" value={f.adultos} onChange={set("adultos")}>
          {[1, 2, 3, 4, 5, 6].map((n) => <option key={n} value={n}>{n}</option>)}
        </select>
      </label>
      <button className="primary" type="submit" disabled={enviando}>{enviando ? "Iniciando…" : "Buscar"}</button>
      <label className="invite">
        Beta com convite
        <input id="convite" value={f.convite} onChange={set("convite")} placeholder="código" autoComplete="off" />
      </label>
      {erro && <p className="error" role="alert">{erro}</p>}
      <p className="muted" style={{ margin: 0 }}>Até {MAX_DATAS} datas por busca, somando ida e volta.</p>
    </form>
  );
}
