"""Config flow for OpenRouter Activity integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OpenRouterApiAuthError, OpenRouterApiError, OpenRouterClient
from .const import (
    CONF_MANAGEMENT_API_KEY,
    CONF_SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    SUPPORTED_SCAN_INTERVAL_MINUTES,
)


class OpenRouterActivityConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OpenRouter Activity."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_MANAGEMENT_API_KEY].strip()
            scan_interval_minutes = int(user_input[CONF_SCAN_INTERVAL_MINUTES])
            session = async_get_clientsession(self.hass)
            client = OpenRouterClient(session=session, api_key=api_key)

            try:
                await client.validate_management_key()
            except OpenRouterApiAuthError:
                errors["base"] = "invalid_auth"
            except OpenRouterApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="OpenRouter Activity",
                    data={
                        CONF_MANAGEMENT_API_KEY: api_key,
                        CONF_SCAN_INTERVAL_MINUTES: scan_interval_minutes,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MANAGEMENT_API_KEY): str,
                    vol.Required(
                        CONF_SCAN_INTERVAL_MINUTES,
                        default=DEFAULT_SCAN_INTERVAL_MINUTES,
                    ): vol.In(SUPPORTED_SCAN_INTERVAL_MINUTES),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OpenRouterActivityOptionsFlowHandler(config_entry)


class OpenRouterActivityOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for OpenRouter Activity."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Allow the user to update the management API key and polling interval."""
        errors: dict[str, str] = {}
        current_api_key = self._config_entry.data.get(CONF_MANAGEMENT_API_KEY, "")
        current_scan_interval = int(
            self._config_entry.options.get(
                CONF_SCAN_INTERVAL_MINUTES,
                self._config_entry.data.get(CONF_SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL_MINUTES),
            )
        )

        if user_input is not None:
            updated_api_key = user_input.get(CONF_MANAGEMENT_API_KEY, "").strip() or current_api_key
            scan_interval_minutes = int(user_input[CONF_SCAN_INTERVAL_MINUTES])

            if updated_api_key != current_api_key:
                session = async_get_clientsession(self.hass)
                client = OpenRouterClient(session=session, api_key=updated_api_key)

                try:
                    await client.validate_management_key()
                except OpenRouterApiAuthError:
                    errors["base"] = "invalid_auth"
                except OpenRouterApiError:
                    errors["base"] = "cannot_connect"
                except Exception:
                    errors["base"] = "unknown"

            if not errors:
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={
                        **self._config_entry.data,
                        CONF_MANAGEMENT_API_KEY: updated_api_key,
                    },
                    options={
                        **self._config_entry.options,
                        CONF_SCAN_INTERVAL_MINUTES: scan_interval_minutes,
                    },
                )
                self.hass.async_create_task(
                    self.hass.config_entries.async_reload(self._config_entry.entry_id)
                )
                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_MANAGEMENT_API_KEY,
                        default=current_api_key,
                    ): str,
                    vol.Required(
                        CONF_SCAN_INTERVAL_MINUTES,
                        default=current_scan_interval,
                    ): vol.In(SUPPORTED_SCAN_INTERVAL_MINUTES),
                }
            ),
            description_placeholders={
                "current_key_hint": f"{current_api_key[:12]}..." if current_api_key else "niet ingesteld",
            },
            errors=errors,
        )
