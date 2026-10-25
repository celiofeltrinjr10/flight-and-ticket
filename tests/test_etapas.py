"""Testes da busca em duas fases e da seleção de combinações. Rodar: python -m unittest -v"""

import unittest
from datetime import date, datetime, timedelta, timezone

from tracker import config
from tracker.collect import Runner
from tracker.models import Itinerary, Segment

T0 = datetime(2026, 11, 10, 10, 0)


def itin(direction, day, airline, price, number="1"):
    seg = Segment("BCN" if direction == "ida" else "GRU", "GRU" if direction == "ida" else "BCN",
                  T0, T0 + timedelta(minutes=600), 600, airline, number, airline_name=airline)
    return Itinerary(direction, day, [seg], [], 600, price, "EUR", "teste", datetime.now(timezone.utc), "",
                     airline_names=[airline])


class SerializacaoTest(unittest.TestCase):
    def test_ida_e_volta_pelo_json(self):
        it = itin("ida", date(2026, 11, 10), "AT", 426.0, "965")
        back = Itinerary.from_dict(it.to_dict())
        self.assertEqual(back.flights, "AT965")
        self.assertEqual(back.segments[0].departure, it.segments[0].departure)
        self.assertEqual(back.price, 426.0)
        self.assertEqual(back.date, it.date)


class CombinacoesTest(unittest.TestCase):
    def test_somente_mesma_cia(self):
        cfg = config.load()
        cfg.somente_mesma_cia = True
        cfg.combinacoes, cfg.vagas_por_destaque = 10, 0
        its = [itin("ida", date(2026, 11, 10), "AT", 400), itin("ida", date(2026, 11, 10), "AZ", 380, "2"),
               itin("volta", date(2027, 1, 10), "AT", 450), itin("volta", date(2027, 1, 10), "AV", 350, "3")]
        picked = Runner(cfg, None, "t").pick_combos(its)
        self.assertTrue(picked)
        for _, o, r in picked:
            self.assertEqual(o.airlines, r.airlines)

    def test_sem_restricao_mistura_companhias(self):
        cfg = config.load()
        cfg.somente_mesma_cia = False
        cfg.combinacoes, cfg.vagas_por_destaque = 10, 0
        its = [itin("ida", date(2026, 11, 10), "AZ", 380), itin("volta", date(2027, 1, 10), "AV", 350)]
        picked = Runner(cfg, None, "t").pick_combos(its)
        self.assertEqual(len(picked), 1)


if __name__ == "__main__":
    unittest.main()
