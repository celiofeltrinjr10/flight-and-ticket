import Link from "next/link";

export const metadata = { title: "Como funciona · Passagens" };

export default function ComoFunciona() {
  return (
    <main className="page prose">
      <div className="top"><Link className="brand" href="/">Passagens</Link></div>
      <h1 style={{ fontSize: "1.6rem" }}>Como funciona</h1>
      <p>Você escolhe a rota e as semanas em que pode viajar. Consultamos cada data e mostramos:</p>
      <ul>
        <li><b>Quando voar</b>: o preço de cada dia, do mais barato ao mais caro.</li>
        <li><b>Qual opção</b>: o preço final, comparando ida e volta na mesma passagem com duas passagens separadas.</li>
        <li><b>Compro agora ou espero?</b>: nas rotas que acompanhamos todo dia, um sinal com base no histórico de preços.</li>
      </ul>
      <p>Só entram voos com no máximo uma escala. Você ajusta o resto nos filtros: horas por voo, horários e companhias.</p>
      <p>Os preços mudam o tempo todo. Confirme sempre no link antes de comprar: não vendemos passagens.</p>
      <p className="muted">Versão beta. Busca aberta para convidados.</p>
    </main>
  );
}
