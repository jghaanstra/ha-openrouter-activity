"""API client for OpenRouter Activity integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import DEFAULT_TIMEOUT_SECONDS

BASE_URL = "https://openrouter.ai"


class OpenRouterApiError(Exception):
    """Base OpenRouter API exception."""

    def __init__(self, message: str, status: int | None = None) -> None:
        """Initialize API error with optional HTTP status."""
        super().__init__(message)
        self.status = status


class OpenRouterApiAuthError(OpenRouterApiError):
    """Raised when API key is invalid or unauthorized."""


@dataclass(slots=True)
class OpenRouterClient:
    """Client for the OpenRouter management APIs."""

    session: ClientSession
    api_key: str

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _request_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform a GET request and return parsed JSON."""
        url = f"{BASE_URL}{path}"

        try:
            async with self.session.get(
                url,
                headers=self._headers,
                params=params,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            ) as response:
                if response.status in (401, 403):
                    raise OpenRouterApiAuthError("Unauthorized")

                response.raise_for_status()
                data = await response.json(content_type=None)
        except OpenRouterApiAuthError:
            raise
        except ClientResponseError as err:
            raise OpenRouterApiError(str(err), status=err.status) from err
        except (ClientError, TimeoutError) as err:
            raise OpenRouterApiError(str(err)) from err

        if not isinstance(data, dict):
            raise OpenRouterApiError("Unexpected API response format")

        return data

    async def validate_management_key(self) -> None:
        """Validate management key by calling credits endpoint."""
        await self.get_credits()

    async def get_credits(self) -> dict[str, float]:
        """Return total credits and total usage."""
        payload = await self._request_json("/api/v1/credits")
        data = payload.get("data", {})

        return {
            "total_credits": float(data.get("total_credits", 0.0) or 0.0),
            "total_usage": float(data.get("total_usage", 0.0) or 0.0),
        }
