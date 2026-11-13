"""Client minimal de l'API HTTP de Frigate."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp


class FrigateApiError(Exception):
    """Erreur de communication avec Frigate."""


class FrigateApi:
    """Appels HTTP vers Frigate (port interne 5000, sans authentification)."""

    def __init__(self, session: aiohttp.ClientSession, url: str) -> None:
        self._session = session
        self._url = url.rstrip("/")

    async def request(
        self, method: str, path: str, json: Any | None = None, timeout: int = 20
    ) -> Any:
        """Envoie une requête et renvoie le JSON (ou le texte) de la réponse."""
        try:
            async with asyncio.timeout(timeout):
                async with self._session.request(
                    method, f"{self._url}/api/{path.lstrip('/')}", json=json
                ) as resp:
                    text = await resp.text()
                    if resp.status >= 400:
                        raise FrigateApiError(f"HTTP {resp.status} : {text[:200]}")
                    try:
                        return await resp.json(content_type=None)
                    except ValueError:
                        return text
        except (aiohttp.ClientError, TimeoutError) as err:
            raise FrigateApiError(str(err) or type(err).__name__) from err

    async def stats(self) -> dict[str, Any]:
        """Statistiques de Frigate."""
        data = await self.request("GET", "stats")
        if not isinstance(data, dict):
            raise FrigateApiError("Réponse de statistiques inattendue")
        return data

    async def version(self) -> str:
        """Version de Frigate."""
        return str(await self.request("GET", "version"))
