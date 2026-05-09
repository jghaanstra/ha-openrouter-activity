"""Constants for the OpenRouter Activity integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "openrouter_activity"
CONF_MANAGEMENT_API_KEY = "management_api_key"
CONF_SCAN_INTERVAL_MINUTES = "scan_interval_minutes"

DEFAULT_SCAN_INTERVAL_MINUTES = 30
DEFAULT_SCAN_INTERVAL = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES)
DEFAULT_TIMEOUT_SECONDS = 20

SUPPORTED_SCAN_INTERVAL_MINUTES: tuple[int, ...] = (15, 30, 60, 120, 360, 1440)

COORDINATOR = "coordinator"
CLIENT = "client"
STORAGE_VERSION = 1

PLATFORMS: list[Platform] = [Platform.SENSOR]

ATTR_BASELINE_MONTH = "baseline_month"
ATTR_BASELINE_USED_CREDITS = "baseline_used_credits"
