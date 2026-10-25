import Link from "next/link";
import { readPublicJson } from "@/lib/github";
import SearchForm from "./SearchForm";

type Index = {
  principal?: { title: string; ida: [string, string]; volta: [string, string] | null; min: number | null; tipo: Tipo; moeda: string };
  buscas?: { slug: string; title: string; min: number | null; tipo: Tipo; parcial?: boolean; moeda: string; ok: boolean; atualizado: string | null }[];
};

const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
const mes = (iso: string) => MESES[Number(iso.slice(5, 7)) - 1];
type Tipo = "conferido" | "2_passagens" | "so_ida" | null;
const TIPO: Record<string, string> = { conferido: "ida e volta ✓", "2_passagens": "ida e volta · 2 passagens", so_ida: "só ida" };
const dia = (d: string) => `${Number(d.slice(6, 8))} ${MESES[Number(d.slice(4, 6)) - 1]}`;
// "BCN-SAO_20261110-20261124_volta-20261208-20261222" → título e datas legíveis
function rotaDoSlug(slug: string) {
  const [par, ida, , volta] = slug.replace("_volta-", "_volta_").split("_");
  const [o, d] = par.split("-");
  const per = (x?: string) => { if (!x) return ""; const [a, b] = x.split("-"); return a === b ? dia(a) : `${dia(a)} – ${dia(b)}`; };
  return { titulo: `${o} ${volta ? "⇄" : "→"} ${d}`, datas: `ida ${per(ida)}${volta ? ` · volta ${per(volta)}` : ""}` };
}
const eur = (v: number | null, m = "EUR") => (v == null ? "—" : `${Math.round(v).toLocaleString("pt-BR")} ${m === "EUR" ? "€" : m}`);

export const revalidate = 300;

export default async function Home() {
  let idx: Index | null = null;
  try {
    idx = await readPublicJson<Index>("index.json", 300);
  } catch {
    idx = null;
  }
  const p = idx?.principal;
  const recentes = (idx?.buscas || []).filter((b) => b.ok).slice(0, 3);

  return (
    <main className="page">
      <div className="top">
        <span className="brand">Passagens</span>
        <Link className="quiet" href="/como-funciona">Como funciona</Link>
      </div>

      <h1>Compro agora ou espero?</h1>
      <p className="lead">
        Diga para onde quer ir e em que semanas. Mostramos o melhor dia para voar, o preço final e a hora de comprar.
      </p>

      <SearchForm />

      {(p || recentes.length > 0) && <p className="label">Acompanhando agora</p>}
      <div className="routes">
        {p && (
          <Link className="route" href="/rota/principal">
            <span>
              BCN ⇄ SAO
              <small>
                ida {mes(p.ida[0])}–{mes(p.ida[1])}
                {p.volta ? ` · volta ${mes(p.volta[0])}–${mes(p.volta[1])}` : ""} · todo dia
              </small>
            </span>
            <span className="price">{eur(p.min, p.moeda)}<small>{TIPO[p.tipo || ""] || ""}</small></span>
          </Link>
        )}
        {recentes.map((b) => {
          const r = rotaDoSlug(b.slug);
          return (
            <Link key={b.slug} className="route" href={`/rota/${b.slug}`}>
              <span>{r.titulo}<small>{r.datas}</small></span>
              <span className="price">{eur(b.min, b.moeda)}<small>{b.parcial ? "conferindo ida e volta…" : TIPO[b.tipo || ""] || ""}</small></span>
            </Link>
          );
        })}
      </div>
    </main>
  );
}
