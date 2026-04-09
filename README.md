# Homgar Home Assistant Integration

This integration connects your RainPoint Smart+ garden devices to Home Assistant through the Homgar API.

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

This integration is based on the [homgarapi](https://github.com/Remboooo/homgarapi) library. For issues with device communication, please also check that repository.

## Support

If you encounter issues:

1. Check the Home Assistant logs for error messages
2. Verify your Homgar account can access devices via the mobile app
3. Create an issue on the GitHub repository with relevant log entries

## Disclaimer

This is an unofficial integration. RainPoint and Homgar are trademarks of their respective owners. This integration is not affiliated with or endorsed by RainPoint.
