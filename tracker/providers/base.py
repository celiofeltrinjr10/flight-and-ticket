"""Interface comum das fontes de dados.

Para adicionar uma fonte nova: crie uma classe que herde de ``Provider``,
implemente ``search_oneway`` (e ``search_roundtrip`` se a fonte tiver ida e
volta) e registre o nome em ``providers/__init__.py``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from ..config import Config
from ..models import Itinerary


class ProviderError(Exception):
    """Falha da fonte (rede, bloqueio, resposta inesperada)."""


@dataclass
class RoundTripQuote:
    """Preço real de ida e volta para uma ida escolhida + uma opção de volta."""

    total_price: float
    ret: Itinerary  # o itinerário de volta; ``ret.price`` = preço total da ida e volta
    link: str


class Provider(ABC):
    name = "base"
    supports_roundtrip = False

    def __init__(self, cfg: Config):
        self.cfg = cfg

    @abstractmethod
    def search_oneway(self, direction: str, day: date) -> list[Itinerary]:
        """Todas as opções só de ida para ``day`` no sentido ``direction``."""

    def search_roundtrip(self, outbound: Itinerary, return_day: date) -> list[RoundTripQuote]:
        """Opções de volta (com preço total) para a ida ``outbound`` já escolhida."""
        raise NotImplementedError(f"a fonte {self.name} não faz busca de ida e volta")

    def close(self) -> None:
        pass
