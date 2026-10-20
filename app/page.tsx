import Link from "next/link";
import { readPublicJson } from "@/lib/github";
import SearchForm from "./SearchForm";

type Index = {
  principal?: { title: string; ida: [string, string]; volta: [string, string] | null; min_ida: number | null; moeda: string };
  buscas?: { slug: string; title: string; min: number | null; moeda: string; ok: boolean; atualizado: string | null }[];
};

const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
const mes = (iso: string) => MESES[Number(iso.slice(5, 7)) - 1];
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
              Barcelona ↔ São Paulo
              <small>
                ida {mes(p.ida[0])}–{mes(p.ida[1])}
                {p.volta ? ` · volta ${mes(p.volta[0])}–${mes(p.volta[1])}` : ""} · todo dia
              </small>
            </span>
            <span className="price"><small>ida desde</small> {eur(p.min_ida, p.moeda)}</span>
          </Link>
        )}
        {recentes.map((b) => (
          <Link key={b.slug} className="route" href={`/rota/${b.slug}`}>
            <span>{b.title}</span>
            <span className="price"><small>desde</small> {eur(b.min, b.moeda)}</span>
          </Link>
        ))}
      </div>
    </main>
  );
}
