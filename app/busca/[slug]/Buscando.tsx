"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

type Etapa = "preparar" | "datas" | "parcial" | "idavolta" | "montar" | null;
type Status = { estado: string; etapa: Etapa; parcialPronto: boolean };

// Tempos médios medidos nas buscas reais (segundos).
const T_PREPARAR = 60;
const T_POR_DATA = 4.5;
const T_IDAVOLTA = 90; // 6 combinações de ida e volta
const T_MONTAR = 20;

export default function Buscando() {
  const { slug } = useParams<{ slug: string }>();
  const q = useSearchParams();
  const router = useRouter();
  const desde = q.get("desde") || "";
  const datas = Number(q.get("datas") || 20);
  const temVolta = slug.includes("_volta-");
  const [orig, dest] = slug.split("_")[0].split("-");
  const total = T_PREPARAR + datas * T_POR_DATA + (temVolta ? T_IDAVOLTA : 0) + T_MONTAR;

  const [st, setSt] = useState<Status>({ estado: "nao_encontrada", etapa: null, parcialPronto: false });
  const [t, setT] = useState(0);
  const [copiado, setCopiado] = useState(false);

  useEffect(() => {
    const tick = setInterval(() => setT((x) => x + 1), 1000);
    return () => clearInterval(tick);
  }, []);

  useEffect(() => {
    let stop = false;
    async function poll() {
      try {
        const r = await fetch(`/api/status/${slug}?desde=${encodeURIComponent(desde)}`, { cache: "no-store" });
        const s = (await r.json()) as Status;
        if (stop) return;
        setSt(s);
        if (s.estado === "concluida") { router.replace(`/rota/${slug}`); return; }
        if (s.estado === "falhou") return;
      } catch {}
      if (!stop) setTimeout(poll, 8_000);
    }
    poll();
    return () => { stop = true; };
  }, [slug, desde, router]);

  // Ordem das etapas na tela (as do robô + a fila).
  const passos: { id: string; texto: string }[] = [
    { id: "fila", texto: "Pedido recebido" },
    { id: "preparar", texto: "Preparando a busca" },
    { id: "datas", texto: `Consultando ${datas} datas` },
    ...(temVolta ? [{ id: "idavolta", texto: "Conferindo ida e volta juntas" }] : []),
    { id: "montar", texto: "Montando o resultado" },
  ];
  const atual =
    st.estado === "concluida" ? passos.length :
    st.estado === "rodando" ? Math.max(1, passos.findIndex((p) => p.id === (st.etapa === "parcial" ? "datas" : st.etapa))) :
    0;
  const pct = st.estado === "concluida" ? 100 : Math.min(95, Math.round((t / total) * 100));
  const restante = Math.max(1, Math.ceil((total - t) / 60));
  const falhou = st.estado === "falhou";

  async function copiar() {
    try { await navigator.clipboard.writeText(location.href); setCopiado(true); } catch {}
  }

  return (
    <main className="page">
      <div className="top"><Link className="brand" href="/">Passagens</Link></div>
      <h1 style={{ marginTop: 28 }}>{falhou ? "Não deu certo desta vez" : `Buscando ${datas} datas`}</h1>

      <div className="board" aria-live="polite">
        <div className="route-row">
          <span>{orig}</span>
          <span className="plane" style={{ ["--p" as string]: `${pct * 0.92}%` }} />
          <span>{dest}</span>
        </div>
        <ol>
          {passos.map((p, i) => {
            const cls = falhou ? (i < atual ? "done" : "later") : i < atual ? "done" : i === atual ? "now" : "later";
            const label = cls === "done" ? "✓ Feito" : cls === "now" ? "● Agora" : "Depois";
            return <li key={p.id} className={cls}><span>{falhou && i === atual ? "✕ Parou" : label}</span>{p.texto}</li>;
          })}
        </ol>
      </div>

      {falhou ? (
        <p><Link className="btn-out" href="/">Voltar e tentar de novo</Link></p>
      ) : (
        <>
          <div className="bigbar" aria-hidden="true"><div style={{ width: `${pct}%` }} /></div>
          <div className="eta">
            <span>{st.estado === "fila" ? "Na fila: outra busca está terminando" : "tempo estimado"}</span>
            <span>≈ <b>{restante} min</b> restantes</span>
          </div>
          {st.parcialPronto && (
            <p style={{ marginTop: 18 }}>
              <Link className="btn-out" href={`/rota/${slug}`}>Ver os preços de cada dia agora →</Link>
            </p>
          )}
          <p className="muted" style={{ marginTop: 18 }}>
            Pode fechar: este link guarda a busca.{" "}
            <button className="btn-out" style={{ padding: "4px 10px", fontSize: ".85rem" }} onClick={copiar}>
              {copiado ? "Link copiado" : "Copiar link"}
            </button>
          </p>
        </>
      )}
    </main>
  );
}
