import { NextResponse } from "next/server";
import { runState } from "@/lib/github";

export async function GET(req: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  if (!/^[A-Za-z0-9_-]{3,120}$/.test(slug)) return NextResponse.json({ estado: "nao_encontrada" }, { status: 400 });
  const since = new URL(req.url).searchParams.get("desde") || new Date(Date.now() - 3600_000).toISOString();
  const st = await runState(slug, since.slice(0, 19) + "Z");
  return NextResponse.json(st, { headers: { "Cache-Control": "no-store" } });
}
