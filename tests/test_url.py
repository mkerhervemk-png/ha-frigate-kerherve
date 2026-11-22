"""Lot 3 : politique d'adresse Frigate."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.frigate_kerherve.api import FrigateApi
from custom_components.frigate_kerherve.const import DEFAULT_URL, DOMAIN
from custom_components.frigate_kerherve.url import UrlInvalideError, valider_url

ACCEPTEES = [
    DEFAULT_URL,
    "http://ccab4aaf-frigate-fa:5000/",
    "http://192.168.1.20:5000",
    "http://10.0.0.5:5000",
    "http://172.30.33.4:5000",
    "http://127.0.0.1:5000",
    "http://localhost:5000",
    "http://[::1]:5000",
    "http://169.254.10.1:5000",
    "https://frigate.local:8971",
]
REFUSEES = [
    "ftp://ccab4aaf-frigate-fa:5000",
    "file:///etc/passwd",
    "http://user:pass@ccab4aaf-frigate-fa:5000",
    "http://8.8.8.8:5000",
    "http://[2001:4860:4860::8888]:5000",
    "http://frigate.example.com:5000",
    "http://ccab4aaf-frigate-fa:5000/?x=1",
    "http://ccab4aaf-frigate-fa:5000/#frag",
    "http://",
    "http://host:99999",
    "pas une url",
    "",
]


@pytest.mark.parametrize("url", ACCEPTEES)
def test_adresses_locales_acceptees(url):
    assert valider_url(url) == url.strip().rstrip("/")


@pytest.mark.parametrize("url", REFUSEES)
def test_adresses_refusees(url):
    with pytest.raises(UrlInvalideError):
        valider_url(url)


def test_port_reel_conserve():
    assert valider_url("http://ccab4aaf-frigate-fa:5000").endswith(":5000")


def test_client_api_refuse_une_adresse_publique():
    with pytest.raises(UrlInvalideError):
        FrigateApi(AsyncMock(), "http://8.8.8.8:5000")


async def test_flux_refuse_adresse_publique_sans_appel_reseau(hass):
    with patch("custom_components.frigate_kerherve.config_flow.FrigateApi.version") as version:
        r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
        r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": "http://8.8.8.8:5000"})
    assert r["type"] is FlowResultType.FORM
    assert r["errors"] == {"base": "invalid_url"}
    version.assert_not_called()


async def test_flux_accepte_adresse_actuelle(hass):
    with patch(
        "custom_components.frigate_kerherve.config_flow.FrigateApi.version",
        AsyncMock(return_value="0.16"),
    ), patch("custom_components.frigate_kerherve.async_setup_entry", AsyncMock(return_value=True)):
        r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
        r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": DEFAULT_URL + "/"})
    assert r["type"] is FlowResultType.CREATE_ENTRY
    assert r["data"] == {"url": DEFAULT_URL}


async def _services(hass):
    from custom_components.frigate_kerherve import async_setup

    await async_setup(hass, {})
    api = AsyncMock()
    api.request = AsyncMock(return_value={"ok": True})
    entry = MockConfigEntry(domain=DOMAIN, data={"url": DEFAULT_URL}, state=config_entries.ConfigEntryState.LOADED)
    entry.add_to_hass(hass)
    entry.runtime_data = type("C", (), {"api": api})()
    return api


async def test_nom_de_visage_encode(hass):
    api = await _services(hass)
    await hass.services.async_call(
        DOMAIN, "delete_faces", {"name": "Maël K/../x", "ids": ["1"]}, blocking=True, return_response=True
    )
    chemin = api.request.await_args.args[1]
    assert chemin == "faces/Ma%C3%ABl%20K%2F..%2Fx/delete"


async def test_classify_nom_encode(hass):
    api = await _services(hass)
    await hass.services.async_call(
        DOMAIN, "classify_face", {"name": "Aelia ?", "training_file": "f.webp"}, blocking=True, return_response=True
    )
    assert api.request.await_args.args[1] == "faces/train/Aelia%20%3F/classify"


@pytest.mark.parametrize(
    ("service", "methode", "chemin", "donnees"),
    [
        ("get_config", "GET", "config", {}),
        ("set_config", "PUT", "config/set", {"config_data": {"a": 1}}),
        ("restart", "POST", "restart", {}),
        ("list_faces", "GET", "faces", {}),
    ],
)
async def test_services_inchanges(hass, service, methode, chemin, donnees):
    api = await _services(hass)
    reponse = service not in ("restart",)
    await hass.services.async_call(DOMAIN, service, donnees, blocking=True, return_response=reponse)
    assert api.request.await_args.args[:2] == (methode, chemin)
