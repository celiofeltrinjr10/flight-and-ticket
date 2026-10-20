"""Google Flights num navegador Chromium sem janela (Playwright).

Mais lento que o google_ff (~6 s por página), mas é o único jeito gratuito de
obter o preço real de ida e volta: desde ago/2026 o Google só entrega esses
resultados pelo JavaScript da própria página. Também serve de reserva para a
etapa A se as requisições simples forem bloqueadas.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from .. import gflights
from ..config import SEAT_CODES
from ..models import Itinerary
from .base import Provider, ProviderError, RoundTripQuote

RPC = "GetShoppingResults"


class GoogleBrowser(Provider):
    name = "google_browser"
    supports_roundtrip = True

    def __init__(self, cfg):
        super().__init__(cfg)
        self._pw = self._browser = self._ctx = None

    def _context(self):
        if self._ctx is None:
            from playwright.sync_api import sync_playwright

            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch()
            self._ctx = self._browser.new_context(locale="en-US")
            self._ctx.add_cookies([{
                "name": gflights.CONSENT_COOKIE_NAME, "value": gflights.CONSENT_COOKIE_VALUE,
                "domain": ".google.com", "path": "/",
            }])
        return self._ctx

    def _load(self, url: str) -> tuple[str, list[list]]:
        """Abre a página; devolve (html, blocos de resultado carregados via JavaScript)."""
        page = self._context().new_page()
        rpc_texts: list[str] = []

        def on_response(r):
            if RPC in r.url:
                try:
                    rpc_texts.append(r.text())
                except Exception:
                    pass

        page.on("response", on_response)
        try:
            page.goto(url, wait_until="networkidle", timeout=60_000)
            if not rpc_texts:  # às vezes a chamada chega depois do "networkidle"
                page.wait_for_timeout(3_000)
            html = page.content()
        except Exception as e:
            raise ProviderError(f"navegador: {e}") from e
        finally:
            page.close()
        payloads = [p for t in rpc_texts for p in gflights.rpc_payloads(t)]
        return html, payloads

    def _itineraries(self, payloads, *, direction, day, link, queried_at) -> list[Itinerary]:
        out = []
        for payload in payloads:
            for row in gflights.raw_rows(payload):
                try:
                    out.append(gflights.row_to_itinerary(
                        row, direction=direction, day=day, source=self.name,
                        queried_at=queried_at, currency=self.cfg.moeda, link=link,
                    ))
                except (IndexError, TypeError, ValueError) as e:
                    raise ProviderError(f"formato inesperado do Google: {e}") from e
        return out

    def search_oneway(self, direction: str, day: date) -> list[Itinerary]:
        cfg = self.cfg
        origin, dest = cfg.rota(direction)
        tfs = gflights.encode_tfs(
            [gflights.encode_leg(day, [origin], [dest], cfg.max_escalas_servidor)],
            one_way=True, adults=cfg.adultos, seat=SEAT_CODES[cfg.classe],
        )
        link = gflights.search_url(tfs, cfg.moeda)
        queried_at = datetime.now(timezone.utc)
        html, payloads = self._load(link)
        if not payloads:  # resultado embutido na página
            payloads = [gflights.page_payload(html)]
        return self._itineraries(payloads, direction=direction, day=day, link=link,
                                 queried_at=queried_at)

    def search_roundtrip(self, outbound: Itinerary, return_day: date) -> list[RoundTripQuote]:
        cfg = self.cfg
        o_out, d_out = cfg.rota("ida")
        o_ret, d_ret = cfg.rota("volta")
        tfs = gflights.encode_tfs(
            [
                gflights.encode_leg(outbound.date, [o_out], [d_out], cfg.max_escalas_servidor,
                                    selected=outbound.segments),
                gflights.encode_leg(return_day, [o_ret], [d_ret], cfg.max_escalas_servidor),
            ],
            one_way=False, adults=cfg.adultos, seat=SEAT_CODES[cfg.classe],
        )
        link = gflights.search_url(tfs, cfg.moeda)
        queried_at = datetime.now(timezone.utc)
        html, payloads = self._load(link)
        if not payloads:
            gflights.page_payload(html)  # levanta erro se for bloqueio/consentimento
            raise ProviderError("a página de ida e volta não carregou resultados")
        rets = self._itineraries(payloads, direction="volta", day=return_day, link=link,
                                 queried_at=queried_at)
        return [RoundTripQuote(total_price=r.price, ret=r, link=link)
                for r in rets if r.price is not None]

    def close(self) -> None:
        for obj, meth in ((self._ctx, "close"), (self._browser, "close"), (self._pw, "stop")):
            if obj is not None:
                try:
                    getattr(obj, meth)()
                except Exception:
                    pass
        self._pw = self._browser = self._ctx = None
