"""Data coordinator for OpenRouter Activity integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import OpenRouterApiAuthError, OpenRouterApiError, OpenRouterClient
from .const import (
    ATTR_BASELINE_DAY,
    ATTR_BASELINE_MONTH,
    ATTR_BASELINE_USED_CREDITS,
    ATTR_BASELINE_USED_CREDITS_DAILY,
    DOMAIN,
    STORAGE_VERSION,
)


class OpenRouterDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator fetching OpenRouter credits and monthly spend."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: OpenRouterClient,
        entry_id: str,
        scan_interval_minutes: int,
    ) -> None:
        """Initialize coordinator."""
        self.client = client
        self.entry_id = entry_id
        self._store = Store(hass, STORAGE_VERSION, f"{DOMAIN}_{entry_id}_baseline")
        self._baseline_day: str | None = None
        self._baseline_month: str | None = None
        self._baseline_used_credits_daily: float | None = None
        self._baseline_used_credits: float | None = None
        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            name="OpenRouter Activity",
            update_interval=timedelta(minutes=scan_interval_minutes),
        )

    async def async_load_baseline(self) -> None:
        """Load stored monthly baseline from Home Assistant storage."""
        stored = await self._store.async_load()
        if not isinstance(stored, dict):
            return

        baseline_day = stored.get(ATTR_BASELINE_DAY)
        baseline_month = stored.get(ATTR_BASELINE_MONTH)
        baseline_used_daily = stored.get(ATTR_BASELINE_USED_CREDITS_DAILY)
        baseline_used = stored.get(ATTR_BASELINE_USED_CREDITS)

        if isinstance(baseline_day, str):
            self._baseline_day = baseline_day

        if isinstance(baseline_month, str):
            self._baseline_month = baseline_month

        if isinstance(baseline_used_daily, (int, float)):
            self._baseline_used_credits_daily = float(baseline_used_daily)

        if isinstance(baseline_used, (int, float)):
            self._baseline_used_credits = float(baseline_used)

    async def _async_save_baseline(self) -> None:
        """Persist monthly baseline."""
        await self._store.async_save(
            {
                ATTR_BASELINE_DAY: self._baseline_day,
                ATTR_BASELINE_MONTH: self._baseline_month,
                ATTR_BASELINE_USED_CREDITS_DAILY: self._baseline_used_credits_daily,
                ATTR_BASELINE_USED_CREDITS: self._baseline_used_credits,
            }
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest credits and derive current-month spend from stored baseline."""
        now = dt_util.now()
        current_day = now.strftime("%Y-%m-%d")
        current_month = now.strftime("%Y-%m")

        try:
            credits = await self.client.get_credits()
        except OpenRouterApiAuthError as err:
            raise UpdateFailed("Authentication failed") from err
        except OpenRouterApiError as err:
            raise UpdateFailed(f"Error communicating with OpenRouter: {err}") from err

        total_usage = float(credits.get("total_usage", 0.0) or 0.0)

        baseline_changed = False

        # Initialize or roll baseline at day boundaries.
        if self._baseline_day != current_day or self._baseline_used_credits_daily is None:
            self._baseline_day = current_day
            self._baseline_used_credits_daily = total_usage
            baseline_changed = True

        # Initialize or roll baseline at month boundaries.
        if self._baseline_month != current_month or self._baseline_used_credits is None:
            self._baseline_month = current_month
            self._baseline_used_credits = total_usage
            baseline_changed = True

        if baseline_changed:
            await self._async_save_baseline()

        baseline_used_daily = float(self._baseline_used_credits_daily or 0.0)
        baseline_used = float(self._baseline_used_credits or 0.0)
        current_day_spend = round(max(total_usage - baseline_used_daily, 0.0), 2)
        current_month_spend = round(max(total_usage - baseline_used, 0.0), 2)

        return {
            "credits": credits,
            "daily": {
                "current_day_spend": current_day_spend,
                ATTR_BASELINE_DAY: self._baseline_day,
                ATTR_BASELINE_USED_CREDITS_DAILY: round(baseline_used_daily, 2),
                "current_total_usage": round(total_usage, 2),
            },
            "monthly": {
                "current_month_spend": current_month_spend,
                ATTR_BASELINE_MONTH: self._baseline_month,
                ATTR_BASELINE_USED_CREDITS: round(baseline_used, 2),
                "current_total_usage": round(total_usage, 2),
            },
        }
