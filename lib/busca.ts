// Validação do formulário de busca e identificador (igual ao de tracker/busca.py).

export const MAX_DATAS = 40; // ida + volta por busca no site (~6 s por data)

export type BuscaInput = {
  origem: string;
  destino: string;
  idaInicio: string;
  idaFim: string;
  voltaInicio?: string;
  voltaFim?: string;
  adultos: number;
};

const IATA = /^[A-Z]{3}$/;
const DATE = /^\d{4}-\d{2}-\d{2}$/;

const days = (a: string, b: string) => Math.round((Date.parse(b) - Date.parse(a)) / 864e5) + 1;
const compact = (d: string) => d.replaceAll("-", "");

export function validate(b: BuscaInput, today: string): string | null {
  if (!IATA.test(b.origem) || !IATA.test(b.destino)) return "Escolha origem e destino.";
  if (b.origem === b.destino) return "Origem e destino precisam ser diferentes.";
  if (!DATE.test(b.idaInicio) || !DATE.test(b.idaFim)) return "Informe o período da ida.";
  if (b.idaInicio < today) return "A ida precisa começar de hoje em diante.";
  if (b.idaFim < b.idaInicio) return "A data final da ida vem antes da inicial.";
  const hasVolta = !!(b.voltaInicio || b.voltaFim);
  if (hasVolta) {
    if (!b.voltaInicio || !b.voltaFim || !DATE.test(b.voltaInicio) || !DATE.test(b.voltaFim)) return "Complete o período da volta.";
    if (b.voltaFim < b.voltaInicio) return "A data final da volta vem antes da inicial.";
    if (b.voltaInicio < b.idaInicio) return "A volta começa antes da ida.";
  }
  if (!Number.isInteger(b.adultos) || b.adultos < 1 || b.adultos > 9) return "Adultos: de 1 a 9.";
  const n = days(b.idaInicio, b.idaFim) + (hasVolta ? days(b.voltaInicio!, b.voltaFim!) : 0);
  if (n > MAX_DATAS) return `Períodos longos demais: ${n} datas. O máximo por busca é ${MAX_DATAS}.`;
  return null;
}

export function slugOf(b: BuscaInput): string {
  let s = `${b.origem}-${b.destino}_${compact(b.idaInicio)}-${compact(b.idaFim)}`;
  if (b.voltaInicio && b.voltaFim) s += `_volta-${compact(b.voltaInicio)}-${compact(b.voltaFim)}`;
  if (b.adultos !== 1) s += `_${b.adultos}adultos`;
  return s;
}

export const LUGARES: { code: string; name: string }[] = [
  { code: "BCN", name: "Barcelona" }, { code: "MAD", name: "Madri" }, { code: "LIS", name: "Lisboa" },
  { code: "OPO", name: "Porto" }, { code: "PAR", name: "Paris" }, { code: "LON", name: "Londres" },
  { code: "ROM", name: "Roma" }, { code: "MIL", name: "Milão" }, { code: "FRA", name: "Frankfurt" },
  { code: "AMS", name: "Amsterdã" }, { code: "BRU", name: "Bruxelas" }, { code: "ZRH", name: "Zurique" },
  { code: "MUC", name: "Munique" }, { code: "VLC", name: "Valência" }, { code: "AGP", name: "Málaga" },
  { code: "SAO", name: "São Paulo" }, { code: "RIO", name: "Rio de Janeiro" }, { code: "BSB", name: "Brasília" },
  { code: "CNF", name: "Belo Horizonte" }, { code: "SSA", name: "Salvador" }, { code: "REC", name: "Recife" },
  { code: "FOR", name: "Fortaleza" }, { code: "POA", name: "Porto Alegre" }, { code: "CWB", name: "Curitiba" },
  { code: "FLN", name: "Florianópolis" }, { code: "NYC", name: "Nova York" }, { code: "MIA", name: "Miami" },
];
