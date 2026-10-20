"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

const TEXTOS: Record<string, string> = {
  fila: "Na fila. Começamos assim que a busca anterior terminar.",
  rodando: "Consultando cada data. Isso leva alguns minutos.",
  nao_encontrada: "Preparando a busca…",
  concluida: "Pronto! Abrindo os resultados…",
  falhou: "A busca falhou. Tente de novo em alguns minutos.",
};

export default function Buscando() {
  const { slug } = useParams<{ slug: string }>();
  const q = useSearchParams();
  const router = useRouter();
  const desde = q.get("desde") || "";
  const datas = Number(q.get("datas") || 20);
  const previsto = Math.max(90, datas * 9 + 120); // segundos: ~9 s por data + preparo
  const [estado, setEstado] = useState("nao_encontrada");
  const [t, setT] = useState(0);

  useEffect(() => {
    const tick = setInterval(() => setT((x) => x + 1), 1000);
    return () => clearInterval(tick);
  }, []);

  useEffect(() => {
    let stop = false;
    async function poll() {
      try {
        const r = await fetch(`/api/status/${slug}?desde=${encodeURIComponent(desde)}`, { cache: "no-store" });
        const { estado } = await r.json();
        if (stop) return;
        setEstado(estado);
        if (estado === "concluida") { router.replace(`/rota/${slug}`); return; }
        if (estado === "falhou") return;
      } catch {}
      if (!stop) setTimeout(poll, 10_000);
    }
    poll();
    return () => { stop = true; };
  }, [slug, desde, router]);

  const pct = estado === "concluida" ? 100 : Math.min(95, Math.round((t / previsto) * 100));
  return (
    <main className="page">
      <div className="top"><Link className="brand" href="/">Passagens</Link></div>
      <div className="status">
        <h1>{estado === "falhou" ? "Não deu certo desta vez" : "Buscando os melhores preços"}</h1>
        <p className="muted">{TEXTOS[estado] || TEXTOS.rodando}</p>
        <div className="bar" aria-hidden="true"><div style={{ width: `${pct}%` }} /></div>
        <p className="muted">
          {estado === "falhou" ? <Link href="/">Voltar e tentar de novo</Link>
            : `Tempo estimado: ~${Math.ceil(previsto / 60)} min. Pode fechar esta página e voltar depois pelo mesmo link.`}
        </p>
      </div>
    </main>
  );
}
