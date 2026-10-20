"""Registro das fontes de dados disponíveis."""

from __future__ import annotations

from importlib import import_module

from ..config import Config
from .base import Provider, ProviderError, RoundTripQuote

_REGISTRY = {
    "google_ff": ("tracker.providers.google_ff", "GoogleFastFlights"),
    "google_browser": ("tracker.providers.google_browser", "GoogleBrowser"),
    "serpapi": ("tracker.providers.serpapi", "SerpApi"),
    "ignav": ("tracker.providers.ignav", "Ignav"),
}


def get_provider(name: str, cfg: Config) -> Provider:
    if name not in _REGISTRY:
        raise ValueError(f"fonte desconhecida: {name} (opções: {', '.join(_REGISTRY)})")
    module, cls = _REGISTRY[name]
    return getattr(import_module(module), cls)(cfg)


__all__ = ["Provider", "ProviderError", "RoundTripQuote", "get_provider"]
