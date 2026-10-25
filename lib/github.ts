// Acesso ao repositório no GitHub: leitura dos dados (data/public) e disparo das buscas.
// Variáveis de ambiente (configuradas na Vercel, nunca no código):
//   GITHUB_TOKEN  token "fine-grained" só deste repositório: Contents (leitura) e Actions (leitura e escrita)
//   GITHUB_REPO   ex. "celiofeltrinjr10/flight-and-ticket"
//   GITHUB_BRANCH ex. "main"

const REPO = process.env.GITHUB_REPO || "celiofeltrinjr10/flight-and-ticket";
// Na prévia de um Pull Request a Vercel informa o branch; assim a prévia usa o robô e os dados do próprio PR.
const BRANCH = process.env.GITHUB_BRANCH || process.env.VERCEL_GIT_COMMIT_REF || "main";
const API = "https://api.github.com";

function headers(extra: Record<string, string> = {}): HeadersInit {
  const h: Record<string, string> = { "X-GitHub-Api-Version": "2022-11-28", ...extra };
  if (process.env.GITHUB_TOKEN) h.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  return h;
}

/** Lê um JSON de data/public/ no repositório. `null` se o arquivo não existe. */
export async function readPublicJson<T>(path: string, revalidate = 60): Promise<T | null> {
  // Com token: API do GitHub (atualização imediata). Sem token: endereço público (cache de ~5 min).
  const res = process.env.GITHUB_TOKEN
    ? await fetch(`${API}/repos/${REPO}/contents/data/public/${path}?ref=${BRANCH}`, {
        headers: headers({ Accept: "application/vnd.github.raw+json" }),
        next: { revalidate },
      })
    : await fetch(`https://raw.githubusercontent.com/${REPO}/${BRANCH}/data/public/${path}`, { next: { revalidate } });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`GitHub respondeu ${res.status} ao ler ${path}`);
  return (await res.json()) as T;
}

/** Dispara o workflow "Busca sob demanda". */
export async function dispatchSearch(inputs: Record<string, string>): Promise<void> {
  if (!process.env.GITHUB_TOKEN) throw new Error("GITHUB_TOKEN não configurado");
  const res = await fetch(`${API}/repos/${REPO}/actions/workflows/busca-sob-demanda.yml/dispatches`, {
    method: "POST",
    headers: headers({ Accept: "application/vnd.github+json", "Content-Type": "application/json" }),
    body: JSON.stringify({ ref: BRANCH, inputs }),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`GitHub recusou a busca (${res.status}): ${(await res.text()).slice(0, 200)}`);
}

export type RunState = "fila" | "rodando" | "concluida" | "falhou" | "nao_encontrada";
export type Etapa = "preparar" | "datas" | "parcial" | "idavolta" | "montar" | null;

// Nomes dos passos do workflow "Busca sob demanda" → etapa mostrada na tela "buscando".
const PASSOS: Record<string, Etapa> = {
  "Preparar": "preparar",
  "Consultar cada data": "datas",
  "Publicar preços de cada dia": "parcial",
  "Conferir ida e volta": "idavolta",
  "Montar o resultado": "montar",
};

type Run = { id: number; display_title: string; status: string; conclusion: string | null };

/** Situação da execução cujo nome contém o identificador da busca, e a etapa em andamento. */
export async function runState(slug: string, since: string): Promise<{ estado: RunState; etapa: Etapa; parcialPronto: boolean }> {
  const h = { headers: headers({ Accept: "application/vnd.github+json" }), cache: "no-store" as const };
  const res = await fetch(`${API}/repos/${REPO}/actions/workflows/busca-sob-demanda.yml/runs?per_page=20&created=>=${since}`, h);
  if (!res.ok) return { estado: "nao_encontrada", etapa: null, parcialPronto: false };
  const body = (await res.json()) as { workflow_runs: Run[] };
  const run = body.workflow_runs.find((r) => r.display_title.includes(slug));
  if (!run) return { estado: "nao_encontrada", etapa: null, parcialPronto: false };
  if (run.status === "completed") {
    return { estado: run.conclusion === "success" ? "concluida" : "falhou", etapa: null, parcialPronto: run.conclusion === "success" };
  }
  if (run.status !== "in_progress") return { estado: "fila", etapa: null, parcialPronto: false };
  let etapa: Etapa = "preparar";
  let parcialPronto = false;
  const jr = await fetch(`${API}/repos/${REPO}/actions/runs/${run.id}/jobs`, h);
  if (jr.ok) {
    const jobs = (await jr.json()) as { jobs: { steps?: { name: string; status: string; conclusion: string | null }[] }[] };
    for (const st of jobs.jobs[0]?.steps || []) {
      const e = PASSOS[st.name];
      if (!e) continue;
      if (st.status === "in_progress") etapa = e;
      if (e === "parcial" && st.status === "completed" && st.conclusion === "success") parcialPronto = true;
    }
  }
  return { estado: "rodando", etapa, parcialPronto };
}
