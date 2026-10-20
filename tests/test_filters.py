"""Testes dos filtros com itinerários fictícios. Rodar: python -m unittest -v"""

import unittest
from datetime import date, datetime, timedelta, timezone

from tracker import config
from tracker.filters import evaluate
from tracker.models import Itinerary, Segment

CFG = config.load()
T0 = datetime(2026, 11, 10, 10, 0)


def seg(o, d, minutes, start=T0, airline="XX", number="1"):
    return Segment(o, d, start, start + timedelta(minutes=minutes), minutes, airline, number)


def itin(segments, direction="ida", price=500.0):
    return Itinerary(direction, date(2026, 11, 10), segments, [60] * (len(segments) - 1),
                     sum(s.duration_min for s in segments), price, "EUR", "teste",
                     datetime.now(timezone.utc), "")


class FiltrosTest(unittest.TestCase):
    def test_direto_ok(self):
        self.assertTrue(evaluate(itin([seg("BCN", "GRU", 675)]), CFG).valid)

    def test_uma_escala_ok(self):
        it = evaluate(itin([seg("BCN", "CMN", 130), seg("CMN", "GRU", 590)]), CFG)
        self.assertTrue(it.valid, it.reason)

    def test_duas_escalas_descartado(self):
        it = evaluate(itin([seg("BCN", "MAD", 90), seg("MAD", "LIS", 70), seg("LIS", "GRU", 600)]), CFG)
        self.assertFalse(it.valid)
        self.assertIn("2 escalas", it.reason)

    def test_trecho_de_16h_exatas_ok(self):
        self.assertTrue(evaluate(itin([seg("BCN", "DOH", 400), seg("DOH", "GRU", 960)]), CFG).valid)

    def test_trecho_acima_de_16h_descartado(self):
        it = evaluate(itin([seg("BCN", "DOH", 400), seg("DOH", "GRU", 961)]), CFG)
        self.assertFalse(it.valid)
        self.assertIn("DOH-GRU", it.reason)

    def test_aeroporto_errado_descartado(self):
        self.assertFalse(evaluate(itin([seg("BCN", "GIG", 650)]), CFG).valid)

    def test_volta_vcp_ok(self):
        self.assertTrue(evaluate(itin([seg("VCP", "BCN", 640)], direction="volta"), CFG).valid)

    def test_sem_preco_descartado(self):
        self.assertFalse(evaluate(itin([seg("BCN", "GRU", 675)], price=None), CFG).valid)

    def test_destaques(self):
        latam = itin([seg("BCN", "GRU", 675, airline="LA")])
        ram = itin([seg("BCN", "CMN", 130, airline="AT"), seg("CMN", "GRU", 590, airline="AT")])
        latam_escala = itin([seg("BCN", "MAD", 90, airline="LA"), seg("MAD", "GRU", 620, airline="LA")])
        self.assertEqual(CFG.destaque(latam).id, "latam")
        self.assertEqual(CFG.destaque(ram).id, "ram")
        self.assertIsNone(CFG.destaque(latam_escala))


if __name__ == "__main__":
    unittest.main()
