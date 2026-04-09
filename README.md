# Homgar Home Assistant Integration

This integration is a corrected version of the bapesupreme/homgar-homeassistant available on Github.
I have downloaded the [bapesupreme/homgar-homeassistant](https://github.com/bapesupreme/homgar-homeassistant) files and they did not work in HA.
I made the corrections as listed below and can confirm that I have a working installation in HA for RainPoiny Smart Rain Sensor – Wi-Fi Control – model:HCS012ARF

<img width="531" height="151" alt="image" src="https://github.com/user-attachments/assets/e8836943-4779-40b5-a798-02744933e16c" />

## What was changed to get the integration working

This implementation includes a number of fixes to make the Homgar custom integration load correctly in Home Assistant, support newer RainPoint hardware, and expose working rain/battery entities.

### 1. Fixed import and config flow loading issues

**Files changed**
- `custom_components/homgar/__init__.py`
- `custom_components/homgar/config_flow.py`
- `custom_components/homgar/api.py`
- `custom_components/homgar/homgar_api/homgarapi/api.py`

**Changes**
- Fixed broken imports that prevented Home Assistant from loading the integration.
- Changed vendored library imports from absolute imports to relative imports:
  - `from homgarapi.devices ...` → `from .devices ...`
  - `from homgarapi.logutil ...` → `from .logutil ...`
- Updated `__init__.py` and `config_flow.py` to import from the local integration wrapper instead of a missing module.
- Removed config-flow validation that depended on unsupported user-info calls.

This resolved the Home Assistant error:

`Config flow could not be loaded: {"message":"Invalid handler specified"}`

and later:

`No module named 'homgarapi'`

---

### 2. Reworked the Home Assistant API wrapper

**File changed**
- `custom_components/homgar/api.py`

**Changes**
- Updated the wrapper to use the bundled vendored API correctly:
  - `HomgarApi()`
  - `login(email, password)`
  - `get_homes()`
  - `get_devices_for_hid(hid)`
  - `get_device_status(hub)`
- Flattened hubs and subdevices into Home Assistant-friendly dictionaries.
- Changed status refresh to pass the full device object, not just a device ID.
- Added proper Home Assistant-facing status values for:
  - `battery_level`
  - `signal_strength`
  - `rain_amount`
  - `rain_hourly`
  - `rain_daily`
  - `rain_7days`
  - `rain_total`
  - `rain_detected`
  - `raw_status`
  - `raw_status_map`

---

### 3. Improved coordinator refresh logic

**File changed**
- `custom_components/homgar/__init__.py`

**Changes**
- Updated the coordinator to call `async_get_device_status(device)` using the full device dictionary.
- Added typing cleanup for the update coordinator data structure.
- Reduced the update interval from 5 minutes to 15 seconds while testing so device updates are visible more quickly.

---

### 4. Fixed brittle status parsing in the vendored device layer

**File changed**
- `custom_components/homgar/homgar_api/homgarapi/devices.py`

**Changes**
- Made parsing more defensive so the integration does not crash on newer payload formats.
- Added support for raw status payloads when values do not follow the older `general;specific` format.
- Fixed general RSSI parsing so malformed or shortened payloads do not crash the integration.
- Added `raw_status` and `raw_status_map` storage for debugging and newer device support.

This resolved parsing errors like:

- `not enough values to unpack (expected 2, got 1)`
- `invalid literal for int() ...`

---

### 5. Added support for newer modelCode 289 hardware

**File changed**
- `custom_components/homgar/homgar_api/homgarapi/devices.py`

**Changes**
- Added a new device class:
  - `RainPointBridgeV2`
- Mapped `modelCode = 289` in `MODEL_CODE_MAPPING`
- Configured the newer device to listen to:
  - `connected`
  - `state`
  - `D01`

This stopped newer RainPoint/Homgar devices from failing setup as unknown models.

---

### 6. Decoded the newer rain-sensor D01 payload

**File changed**
- `custom_components/homgar/api.py`

**Changes**
- Added decoding logic for the newer binary/hex payload returned in `D01`
- Converted the payload from:
  - `10#E10000FD040000FD050E01FD060E01DC01970E010000`
  into bytes
- Parsed `0xFD` tagged values
- Extracted rain counters from tags `FD 05` and `FD 06`
- Converted values from tenths of a millimeter into `mm`

This was verified against the HomGar app by pouring water into the sensor and confirming that the decoded `27.0 mm` value matched the app.

---

### 7. Added additional rain sensors

**Files changed**
- `custom_components/homgar/const.py`
- `custom_components/homgar/api.py`
- `custom_components/homgar/sensor.py`

**Changes**
- Added support for these rain sensors:
  - `Rain Past Hour`
  - `Rain Past 24 Hours`
  - `Rain Past 7 Days`
  - `Rain Total`
- Exposed `Rain Detected` as a binary sensor
- Added `raw_status` and `raw_status_map` as extra attributes for troubleshooting

---

### 8. Added binary sensor support for rain detection

**Files changed**
- `custom_components/homgar/binary_sensor.py`
- `custom_components/homgar/sensor.py`

**Changes**
- Extended binary sensor attributes to include:
  - `raw_status`
  - `raw_status_map`
- Added `rain_detected` mapping to surface current rain state in Home Assistant

---

### 9. Cleaned up const/entity definitions

**File changed**
- `custom_components/homgar/const.py`

**Changes**
- Added new rain sensor definitions
- Removed unsupported `signal_strength` device class assignment for better HA compatibility

---

## Current result

With these changes, the integration now:

- loads correctly in Home Assistant
- creates the config flow correctly
- discovers the device successfully
- supports newer `modelCode 289` hardware
- creates working rain entities
- decodes rain values from the newer D01 payload
- exposes battery, signal strength, and raw diagnostic attributes

## Notes / known limitations

- Battery percentage on newer devices is still heuristic because the first field in `state` appears to behave more like a battery/status code than a true percentage.
- The rain payload decoding works for the tested newer rain sensor, but other newer models may still need additional reverse engineering.

# Origninal Bapesupreme Notes

## Supported Devices

- **RainPoint Smart+ Irrigation Display Hub** (HWS019WRF-V2)
- **RainPoint Smart+ 2-Zone Water Timer** (HTV213FRF)
- **RainPoint Smart+ Soil & Moisture Sensor** (HCS021FRF)
- **RainPoint Smart+ High Precision Rain Sensor** (HCS012ARF)
- **RainPoint Smart+ Outdoor Air Humidity Sensor** (HCS014ARF)

## Installation

### HACS Installation (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add the repository URL: `https://github.com/bapesupreme/homgar-homeassistant`
6. Select "Integration" as the category
7. Click "Add"
8. Find "Homgar Smart Garden" in the list and install it
9. Restart Home Assistant

### Manual Installation

1. Copy the `homgar` folder from this repository to your `custom_components` directory
2. Restart Home Assistant

## Configuration

### Prerequisites

1. **Create a separate API account** (recommended):
   - Log out from your main Homgar account in the mobile app
   - Create a new account with a different email
   - Log back into your main account
   - Go to 'Me' → 'Home management' → your home → 'Members'
   - Invite your new API account
   - Log into the new account and accept the invite

   > **Note**: Logging in via the API will log you out of the mobile app. Using a separate account prevents this issue.

2. **Install the homgarapi library**:
   ```bash
   pip install homgarapi
   ```

### Setup in Home Assistant

1. Go to **Configuration** → **Integrations**
2. Click the **+** button to add a new integration
3. Search for "Homgar Smart Garden"
4. Enter your Homgar account credentials:
   - **Email**: Your Homgar account email (preferably the API account)
   - **Password**: Your Homgar account password
5. Click **Submit**

The integration will automatically discover all your RainPoint Smart+ devices and create the appropriate sensors and binary sensors.

## Entities Created

### Sensors

**Soil & Moisture Sensor (HCS021FRF)**:
- Soil Moisture (%)
- Soil Temperature (°C)
- Battery Level (%)

**Rain Sensor (HCS012ARF)**:
- Rain Amount (mm)
- Battery Level (%)

**Humidity Sensor (HCS014ARF)**:
- Humidity (%)
- Temperature (°C)
- Battery Level (%)

**Water Timer (HTV213FRF)**:
- Battery Level (%)

**Hub (HWS019WRF-V2)**:
- Signal Strength (dBm)

### Binary Sensors

**Water Timer (HTV213FRF)**:
- Watering Zone 1 (on/off)
- Watering Zone 2 (on/off)

**Rain Sensor (HCS012ARF)**:
- Rain Detected (on/off)

## Automation Examples

### Water Plants When Soil is Dry

```yaml
automation:
  - alias: "Water Garden When Soil Dry"
    trigger:
      - platform: numeric_state
        entity_id: sensor.garden_soil_moisture
        below: 30
    condition:
      - condition: state
        entity_id: binary_sensor.garden_rain_detected
        state: 'off'
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "Garden soil moisture is low ({{ states('sensor.garden_soil_moisture') }}%). Consider watering."
```

### Stop Watering When Rain is Detected

```yaml
automation:
  - alias: "Stop Watering When Rain Detected"
    trigger:
      - platform: state
        entity_id: binary_sensor.garden_rain_detected
        to: 'on'
    condition:
      - condition: or
        conditions:
          - condition: state
            entity_id: binary_sensor.garden_watering_zone_1
            state: 'on'
          - condition: state
            entity_id: binary_sensor.garden_watering_zone_2
            state: 'on'
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "Rain detected! Automatic watering has been paused."
```

### Low Battery Alert

```yaml
automation:
  - alias: "Garden Sensor Low Battery Alert"
    trigger:
      - platform: numeric_state
        entity_id: 
          - sensor.soil_sensor_battery
          - sensor.rain_sensor_battery
          - sensor.humidity_sensor_battery
          - sensor.water_timer_battery
        below: 20
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "{{ trigger.to_state.attributes.friendly_name }} battery is low ({{ trigger.to_state.state }}%)"
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify your email and password are correct
   - Make sure you're using the API account if you created one
   - Check if your account has access to the home with the devices

2. **No Devices Found**:
   - Ensure your devices are properly set up in the Homgar mobile app
   - Check that devices are online and connected to the hub
   - Try refreshing the integration

3. **Entities Not Updating**:
   - Check the integration logs for errors
   - Verify your internet connection
   - The integration updates every 5 minutes by default

### Enable Debug Logging

Add the following to your `configuration.yaml` to enable debug logging:

```yaml
logger:
  default: warning
  logs:
    custom_components.homgar: debug
    homgarapi: debug
```

## API Rate Limiting

The integration updates device data every 5 minutes to avoid overwhelming the Homgar API. This interval can be adjusted by modifying the `UPDATE_INTERVAL` constant in the integration code.

## Contributing

This integration is based on the [homgarapi](https://github.com/Remboooo/homgarapi) library and correction of [bapesupreme/homgar-homeassistant](https://github.com/bapesupreme/homgar-homeassistant). For issues with device communication, please also check that repository.

## Support

If you encounter issues:

1. Check the Home Assistant logs for error messages
2. Verify your Homgar account can access devices via the mobile app
3. Create an issue on the GitHub repository with relevant log entries

## Disclaimer

This is an unofficial integration. RainPoint and Homgar are trademarks of their respective owners. This integration is not affiliated with or endorsed by RainPoint.
