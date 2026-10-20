import { readFile } from "node:fs/promises";
import path from "node:path";
import { readPublicJson } from "@/lib/github";

// Página de resultados: o painel aprovado (painel.html) com os dados mais recentes do repositório.
// "principal" = rota acompanhada todo dia; demais = buscas feitas pelo site ou pelo GitHub.
export async function GET(_req: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  if (!/^[A-Za-z0-9_-]{3,120}$/.test(slug)) return new Response("Página não encontrada", { status: 404 });
  const file = slug === "principal" ? "rotas/principal.json" : `buscas/${slug}.json`;
  const data = await readPublicJson<Record<string, unknown>>(file, 60);
  if (!data) return new Response("Ainda não há resultados para esta busca.", { status: 404, headers: { "Content-Type": "text/plain; charset=utf-8" } });
  data.links = { inicio: "/" };
  const template = await readFile(path.join(process.cwd(), "painel.html"), "utf-8");
  const payload = JSON.stringify(data).replace(/<\//g, "<\\/");
  return new Response(template.replace("/*__DATA__*/null", payload), {
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "public, s-maxage=60, stale-while-revalidate=300" },
  });
}
