# Arvee for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/ThisSmartHouse/hass-arvee.svg)](https://github.com/ThisSmartHouse/hass-arvee/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Home Assistant integration designed for mobile installations (RVs, boats, etc.) that automatically keeps your Home Assistant location and timezone in sync with your GPS position.

## Features

- **Automatic Location Tracking**: Configure GPS entities and Arvee automatically updates Home Assistant's home location
- **Automatic Timezone Updates**: Timezone is automatically determined based on your coordinates using offline lookup
- **Configurable Threshold**: Set a minimum distance (in miles) before updates are triggered to avoid constant updates
- **Manual Services**: Services available for manual timezone/location control via automations

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right and select "Custom repositories"
4. Add `https://github.com/ThisSmartHouse/hass-arvee` as an Integration
5. Search for "Arvee" and install it
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/arvee` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

### Via UI (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Arvee"
4. Select your latitude and longitude entities (from a GPS tracker, phone, etc.)
5. Set the update threshold (minimum distance in miles before updating)

### GPS Entity Sources

Arvee works with any entity that provides numeric latitude/longitude values:

- **Device Trackers**: Phone GPS via Home Assistant Companion app
- **Sensors**: Dedicated GPS sensors, OBD-II adapters, etc.
- **Input Numbers**: For testing or manual control

## Services

### `arvee.set_timezone`

Manually set the Home Assistant timezone.

| Field | Description | Example |
|-------|-------------|---------|
| `timezone` | IANA timezone string | `America/New_York` |

### `arvee.set_geo_timezone`

Manually set location and timezone based on coordinates.

| Field | Description | Example |
|-------|-------------|---------|
| `latitude` | Latitude coordinate | `40.7128` |
| `longitude` | Longitude coordinate | `-74.0060` |

## How It Works

1. Arvee monitors the configured latitude/longitude entities for state changes
2. When a change is detected, it calculates the distance from the last known position
3. If the distance exceeds the configured threshold, it:
   - Updates Home Assistant's home latitude/longitude
   - Looks up the timezone for the new coordinates (using `tzfpy` - fully offline)
   - Updates Home Assistant's timezone

## Notes

- **Timezone Display**: Home Assistant's UI uses friendly names for timezones (e.g., "Eastern Time" for `America/New_York`). If you're in a less common timezone, the dropdown in Settings may appear blank, but the timezone is still correctly set.
- **Offline Operation**: Timezone lookups are performed entirely offline using the `tzfpy` library - no internet connection required.

## Troubleshooting

### Timezone not updating

1. Check that your GPS entities have valid numeric values
2. Verify the distance threshold isn't set too high
3. Check the Home Assistant logs for any Arvee-related errors

### Entity not found errors

Make sure your GPS entities exist and are available before configuring Arvee.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details.
