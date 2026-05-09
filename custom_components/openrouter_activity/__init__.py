"""The OpenRouter Activity integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OpenRouterClient
from .const import (
    CLIENT,
    CONF_MANAGEMENT_API_KEY,
    CONF_SCAN_INTERVAL_MINUTES,
    COORDINATOR,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import OpenRouterDataUpdateCoordinator


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up integration from YAML (unused)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OpenRouter Activity from a config entry."""
    session = async_get_clientsession(hass)
    api_key: str = entry.data[CONF_MANAGEMENT_API_KEY]
    scan_interval_minutes = int(
        entry.options.get(
            CONF_SCAN_INTERVAL_MINUTES,
            entry.data.get(CONF_SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL_MINUTES),
        )
    )

    client = OpenRouterClient(session=session, api_key=api_key)
    coordinator = OpenRouterDataUpdateCoordinator(
        hass=hass,
        client=client,
        entry_id=entry.entry_id,
        scan_interval_minutes=scan_interval_minutes,
    )
    await coordinator.async_load_baseline()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        CLIENT: client,
        COORDINATOR: coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
