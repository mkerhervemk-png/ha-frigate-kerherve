"""Validation de l'adresse Frigate : limite les destinations HTTP possibles.

Politique :
- schéma http ou https uniquement ;
- pas d'identifiants intégrés, ni requête (?) ni fragment (#) ;
- hôte : adresse IP privée, loopback ou link-local, ou nom DNS local
  (nom de service Docker sans point, ou domaine en .local) ;
- le port réel de l'installation est conservé.
"""

from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit


class UrlInvalideError(ValueError):
    """Adresse Frigate refusée."""


def valider_url(url: str) -> str:
    """Renvoie l'URL normalisée, ou lève UrlInvalideError."""
    url = (url or "").strip().rstrip("/")
    try:
        parts = urlsplit(url)
        parts.port  # noqa: B018 - lève ValueError si le port est invalide
    except ValueError as err:
        raise UrlInvalideError("adresse malformée") from err
    if parts.scheme not in ("http", "https"):
        raise UrlInvalideError("seuls http et https sont autorisés")
    if parts.username is not None or parts.password is not None:
        raise UrlInvalideError("identifiants dans l'adresse interdits")
    if parts.query or parts.fragment or "?" in url or "#" in url:
        raise UrlInvalideError("requête ou fragment interdit")
    host = (parts.hostname or "").lower()
    if not host:
        raise UrlInvalideError("hôte manquant")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        # Nom DNS : seulement les noms locaux explicitement admis.
        if "." in host and not host.endswith(".local"):
            raise UrlInvalideError("nom DNS externe refusé") from None
    else:
        if not (ip.is_private or ip.is_loopback or ip.is_link_local):
            raise UrlInvalideError("adresse IP publique refusée")
    return url
