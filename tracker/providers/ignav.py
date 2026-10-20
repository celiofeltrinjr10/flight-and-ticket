"""Lugar reservado para a API da Ignav.

Ainda não implementada: preciso da documentação da API e de uma chave
(IGNAV_API_KEY) para escrever e testar. O formato a seguir é o de
``serpapi.py``: converter cada opção em ``Itinerary``/``Segment``.
"""

from __future__ import annotations

import os

from .base import Provider, ProviderError


class Ignav(Provider):
    name = "ignav"

    def __init__(self, cfg):
        super().__init__(cfg)
        if not os.environ.get("IGNAV_API_KEY"):
            raise ProviderError("variável de ambiente IGNAV_API_KEY não definida")
        raise ProviderError("fonte Ignav ainda não implementada")

    def search_oneway(self, direction, day):  # pragma: no cover
        raise NotImplementedError
