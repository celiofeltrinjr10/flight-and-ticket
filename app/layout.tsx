import type { Metadata, Viewport } from "next";
import { Barlow, Barlow_Condensed } from "next/font/google";
import "./globals.css";

// Identidade "cartão de embarque + painel de partidas" (produto/revisoes/2026-10-20-ui.md).
const barlow = Barlow({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-text" });
const barlowCond = Barlow_Condensed({ subsets: ["latin"], weight: ["600", "700"], variable: "--font-display" });

export const metadata: Metadata = {
  title: "Compro agora ou espero? · Passagens",
  description: "Diga para onde quer ir e em que semanas. Mostramos o melhor dia para voar, o preço final e a hora de comprar.",
};

export const viewport: Viewport = { width: "device-width", initialScale: 1, viewportFit: "cover" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className={`${barlow.variable} ${barlowCond.variable}`}>
      <body>{children}</body>
    </html>
  );
}
