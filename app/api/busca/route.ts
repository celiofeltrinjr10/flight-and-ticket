import { NextResponse } from "next/server";
import { dispatchSearch } from "@/lib/github";
import { slugOf, validate, type BuscaInput } from "@/lib/busca";

// Durante o beta a busca exige um código de convite (variável INVITE_CODE na Vercel).
export async function POST(req: Request) {
  let body: Partial<BuscaInput> & { convite?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ erro: "Pedido inválido." }, { status: 400 });
  }
  const invite = process.env.INVITE_CODE;
  if (!invite || (body.convite || "").trim() !== invite) {
    return NextResponse.json({ erro: "Código de convite inválido." }, { status: 401 });
  }
  const b: BuscaInput = {
    origem: String(body.origem || "").toUpperCase(),
    destino: String(body.destino || "").toUpperCase(),
    idaInicio: String(body.idaInicio || ""),
    idaFim: String(body.idaFim || body.idaInicio || ""),
    voltaInicio: body.voltaInicio ? String(body.voltaInicio) : undefined,
    voltaFim: body.voltaFim ? String(body.voltaFim) : body.voltaInicio ? String(body.voltaInicio) : undefined,
    adultos: Number(body.adultos || 1),
  };
  const today = new Date().toISOString().slice(0, 10);
  const erro = validate(b, today);
  if (erro) return NextResponse.json({ erro }, { status: 400 });

  const slug = slugOf(b);
  try {
    await dispatchSearch({
      origem: b.origem,
      destino: b.destino,
      ida: `${b.idaInicio} a ${b.idaFim}`,
      volta: b.voltaInicio ? `${b.voltaInicio} a ${b.voltaFim}` : "",
      adultos: String(b.adultos),
      classe: "economy",
      max_escalas: "1",
      moeda: "EUR",
      data_limite: "",
      slug,
    });
  } catch (e) {
    console.error(e);
    return NextResponse.json({ erro: "Não foi possível iniciar a busca agora. Tente de novo em instantes." }, { status: 502 });
  }
  return NextResponse.json({ slug, desde: new Date(Date.now() - 60_000).toISOString() });
}
