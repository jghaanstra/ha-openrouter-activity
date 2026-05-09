# OpenRouter Activity - Home Assistant Integration

> Disclaimer: This extension was created through vibe coding and community-driven iteration and provides only basic functionality. Use at your own risk.

<p align="center">
  <img src="custom_components/openrouter_activity/icon.svg" alt="OpenRouter Activity" width="128"/>
</p>

This integration adds sensors with information about your OpenRouter activity. Currently available sensors are:
| Sensor | Unit | Description |
|---|---|---|
| OpenRouter Total Credits | USD | Total purchased credits value reported by OpenRouter |
| OpenRouter Used Credits | USD | Total used credits value reported by OpenRouter |
| OpenRouter Remaining Credits | USD | `total_credits - total_usage`, never below 0 |
| OpenRouter Current Month Spend | USD | Credits spent in the current month, derived from used-credits delta |

All monetary values are rounded to 2 decimals.


## Requirements

- Home Assistant 2024.6 or newer
- An OpenRouter Management API key

## Installation

### Create a Management API key

1. Go to [openrouter.ai/settings/management-keys](https://openrouter.ai/settings/management-keys)
2. Click Create New Key
3. Copy the generated key (typically starts with `sk-or-ma-`)

### Via HACS (recommended)

1. Add this repository as a Custom Repository in HACS (type: Integration)
2. Install OpenRouter Activity
3. Restart Home Assistant
4. Go to Settings > Devices & Services > Add Integration
5. Search for OpenRouter Activity and enter your Management API key

### Manual

1. Copy `custom_components/openrouter_activity` into your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Settings > Devices & Services > Add Integration
4. Search for OpenRouter Activity and enter your Management API key

## Configuration

During onboarding you configure:

- Management API key
- Polling interval (15, 30, 60, 120, 360, 1440 minutes)

Default polling interval is 30 minutes.

You can edit both values later via the integration settings (gear icon). The integration reloads automatically after saving.


### Current Month Spend sensor attributes

| Attribute | Description |
|---|---|
| `baseline_month` | Baseline month in `YYYY-MM` format |
| `baseline_used_credits` | Stored used-credits value at month start |
| `current_total_usage` | Latest total used credits from OpenRouter |

## How Current Month Spend Is Calculated

This integration does not use activity/generation endpoints anymore.

At each refresh:

1. Call `GET /api/v1/credits`
2. Read `total_usage`
3. Load or maintain a persisted monthly baseline:
   - `baseline_month`
   - `baseline_used_credits`
4. If month changed, reset baseline to current `total_usage`
5. Compute:
   - `current_month_spend = max(total_usage - baseline_used_credits, 0)`

The baseline is stored persistently in Home Assistant storage, so it survives restarts.

### First run behavior

If you install mid-month, the baseline is initialized with the current `total_usage`. That means Current Month Spend starts at 0 from that moment and accumulates forward.

## Notes

- Single-instance integration (one config entry)
- Polling options: 15, 30, 60, 120, 360, 1440 minutes (default: 30)
- Current month logic uses Home Assistant local timezone
- Monetary values are represented in USD
