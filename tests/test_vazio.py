"""Resposta vazia do Google: tenta de novo e usa a fonte reserva. Rodar: python -m unittest -v"""

import unittest
from datetime import date
from unittest import mock

from tracker import config
from tracker.collect import Runner
from tracker.gflights import EmptyResult


class FakeProvider:
    def __init__(self, results):
        self.results = list(results)
        self.calls = 0

    def search_oneway(self, direction, day):
        self.calls += 1
        r = self.results.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    def close(self):
        pass


def runner_with(primary, reserve):
    cfg = config.load()
    cfg.pausa, cfg.espera_base_s = (0, 0), 0
    r = Runner(cfg, None, "t")
    r._providers = {cfg.fonte_a: primary, cfg.fonte_a_reserva: reserve}
    return r


class VazioTest(unittest.TestCase):
    @mock.patch("tracker.collect.time.sleep", lambda s: None)
    def test_vazio_tenta_de_novo_e_usa_reserva(self):
        primary = FakeProvider([EmptyResult("vazio"), EmptyResult("vazio")])
        reserve = FakeProvider([[]])
        r = runner_with(primary, reserve)
        r.stage_a({"ida": [date(2026, 12, 20)]})
        self.assertEqual(primary.calls, 2)  # 1 tentativa + 1 nova tentativa, não 3
        self.assertEqual(reserve.calls, 1)  # depois a fonte reserva
        self.assertEqual(len(r.errors), 2)  # cada resposta vazia fica registrada

    @mock.patch("tracker.collect.time.sleep", lambda s: None)
    def test_vazio_que_se_resolve_na_segunda_tentativa(self):
        primary = FakeProvider([EmptyResult("vazio"), []])
        reserve = FakeProvider([])
        r = runner_with(primary, reserve)
        r.stage_a({"ida": [date(2026, 12, 20)]})
        self.assertEqual(primary.calls, 2)
        self.assertEqual(reserve.calls, 0)
        self.assertEqual(r.failures, 0)


if __name__ == "__main__":
    unittest.main()
