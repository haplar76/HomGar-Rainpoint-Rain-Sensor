import re
from typing import List

STATS_VALUE_REGEX = re.compile(r'^(\d+)\((\d+)/(\d+)/(\d+)\)')


def _parse_stats_value(s):
    if match := STATS_VALUE_REGEX.fullmatch(s):
        return int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
    else:
        return None, None, None, None


def _temp_to_mk(f):
    return round(1000 * ((int(f) * .1 - 32) * 5 / 9 + 273.15))


class HomgarHome:
    """
    Represents a home in Homgar.
    A home can have a number of hubs, each of which can contain sensors/controllers (subdevices).
    """
    def __init__(self, hid, name):
        self.hid = hid
        self.name = name


class HomgarDevice:
    """
    Base class for Homgar devices; both hubs and subdevices.
    Each device has a model (name and code), name, some identifiers and may have alerts.
    """

    FRIENDLY_DESC = "Unknown HomGar device"

    def __init__(self, model, model_code, name, did, mid, alerts, **kwargs):
        self.model = model
        self.model_code = model_code
        self.name = name
        self.did = did
        self.mid = mid
        self.alerts = alerts

        self.address = None
        self.rf_rssi = None
        self.raw_status = None

    def __str__(self):
        return f'{self.FRIENDLY_DESC} "{self.name}" (DID {self.did})'

    def get_device_status_ids(self) -> List[str]:
        return []

    def set_device_status(self, api_obj: dict) -> None:
        if api_obj['id'] == f"D{self.address:02d}":
            self._parse_status_d_value(api_obj['value'])

    def _parse_status_d_value(self, val: str) -> None:
        if ";" not in val:
            self.raw_status = val
            return

        general_str, specific_str = val.split(";", 1)
        self._parse_general_status_d_value(general_str)
        self._parse_device_specific_status_d_value(specific_str)

    def _parse_general_status_d_value(self, s: str):
        parts = [p.strip() for p in str(s).split(",") if p.strip()]
        if len(parts) >= 2:
            try:
                self.rf_rssi = int(parts[1])
            except ValueError:
                self.rf_rssi = None

    def _parse_device_specific_status_d_value(self, s: str):
        raise NotImplementedError()


class HomgarHubDevice(HomgarDevice):
    def __init__(self, subdevices, **kwargs):
        super().__init__(**kwargs)
        self.address = 1
        self.subdevices = subdevices

    def __str__(self):
        return f"{super().__str__()} with {len(self.subdevices)} subdevices"

    def _parse_device_specific_status_d_value(self, s):
        pass


class HomgarSubDevice(HomgarDevice):
    def __init__(self, address, port_number, **kwargs):
        super().__init__(**kwargs)
        self.address = address
        self.port_number = port_number

    def __str__(self):
        return f"{super().__str__()} at address {self.address}"

    def get_device_status_ids(self):
        return [f"D{self.address:02d}"]

    def _parse_device_specific_status_d_value(self, s):
        pass


class RainPointDisplayHub(HomgarHubDevice):
    MODEL_CODES = [264]
    FRIENDLY_DESC = "Irrigation Display Hub"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.wifi_rssi = None
        self.battery_state = None
        self.connected = None
        self.raw_status = None
        self.raw_status_map = {}

        self.temp_mk_current = None
        self.temp_mk_daily_max = None
        self.temp_mk_daily_min = None
        self.temp_trend = None
        self.hum_current = None
        self.hum_daily_max = None
        self.hum_daily_min = None
        self.hum_trend = None
        self.press_pa_current = None
        self.press_pa_daily_max = None
        self.press_pa_daily_min = None
        self.press_trend = None

    def get_device_status_ids(self):
        return ["connected", "state", "D01"]

    def set_device_status(self, api_obj):
        dev_id = api_obj["id"]
        val = api_obj.get("value")

        self.raw_status_map[dev_id] = val

        if dev_id == "state":
            parts = [p.strip() for p in str(val).split(",") if p.strip()]
            if len(parts) >= 1:
                try:
                    battery_code = int(parts[0])
                    
                    if battery_code == 0:
                        self.battery_state = 100
                    elif battery_code == 1:
                        self.battery_state = 50
                    elif battery_code == 2:
                        self.battery_state = 10
                    else:
                        self.battery_state = None
                except ValueError:
                    self.battery_state = None
            if len(parts) >= 2:
                try:
                    self.rf_rssi = int(parts[1])
                except ValueError:
                    self.rf_rssi = None
            return

        if dev_id == "connected":
            try:
                self.connected = int(val) == 1
            except (TypeError, ValueError):
                self.connected = None
            return

        if dev_id == "D01":
            self.raw_status = val
            return

        self.raw_status = val

    def _parse_device_specific_status_d_value(self, s):
        temp_str, hum_str, press_str, *_ = s.split(",")
        self.temp_mk_current, self.temp_mk_daily_max, self.temp_mk_daily_min, self.temp_trend = [
            _temp_to_mk(v) for v in _parse_stats_value(temp_str)
        ]
        self.hum_current, self.hum_daily_max, self.hum_daily_min, self.hum_trend = _parse_stats_value(hum_str)
        self.press_pa_current, self.press_pa_daily_max, self.press_pa_daily_min, self.press_trend = _parse_stats_value(press_str[2:])

    def __str__(self):
        s = super().__str__()
        if self.temp_mk_current:
            s += f": {self.temp_mk_current*1e-3:.1f}K / {self.hum_current}% / {self.press_pa_current}Pa"
        return s


class RainPointSoilMoistureSensor(HomgarSubDevice):
    MODEL_CODES = [72]
    FRIENDLY_DESC = "Soil Moisture Sensor"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.temp_mk_current = None
        self.moist_percent_current = None
        self.light_lux_current = None

    def _parse_device_specific_status_d_value(self, s):
        temp_str, moist_str, light_str = s.split(',')
        self.temp_mk_current = _temp_to_mk(temp_str)
        self.moist_percent_current = int(moist_str)
        self.light_lux_current = int(light_str[2:]) * .1

    def __str__(self):
        s = super().__str__()
        if self.temp_mk_current:
            s += f": {self.temp_mk_current*1e-3-273.15:.1f}°C / {self.moist_percent_current}% / {self.light_lux_current:.1f}lx"
        return s


class RainPointRainSensor(HomgarSubDevice):
    MODEL_CODES = [87]
    FRIENDLY_DESC = "High Precision Rain Sensor"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rainfall_mm_total = None
        self.rainfall_mm_hour = None
        self.rainfall_mm_daily = None
        self.rainfall_mm_7days = None

    def _parse_device_specific_status_d_value(self, s):
        self.rainfall_mm_total, self.rainfall_mm_hour, self.rainfall_mm_daily, self.rainfall_mm_7days = [
            .1 * v for v in _parse_stats_value(s[2:])
        ]

    def __str__(self):
        s = super().__str__()
        if self.rainfall_mm_total:
            s += f": {self.rainfall_mm_total}mm total / {self.rainfall_mm_hour}mm 1h / {self.rainfall_mm_daily}mm 24h / {self.rainfall_mm_7days}mm 7days"
        return s


class RainPointAirSensor(HomgarSubDevice):
    MODEL_CODES = [262]
    FRIENDLY_DESC = "Outdoor Air Humidity Sensor"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.temp_mk_current = None
        self.temp_mk_daily_max = None
        self.temp_mk_daily_min = None
        self.temp_trend = None
        self.hum_current = None
        self.hum_daily_max = None
        self.hum_daily_min = None
        self.hum_trend = None

    def _parse_device_specific_status_d_value(self, s):
        temp_str, hum_str, *_ = s.split(',')
        self.temp_mk_current, self.temp_mk_daily_max, self.temp_mk_daily_min, self.temp_trend = [
            _temp_to_mk(v) for v in _parse_stats_value(temp_str)
        ]
        self.hum_current, self.hum_daily_max, self.hum_daily_min, self.hum_trend = _parse_stats_value(hum_str)

    def __str__(self):
        s = super().__str__()
        if self.temp_mk_current:
            s += f": {self.temp_mk_current*1e-3-273.15:.1f}°C / {self.hum_current}%"
        return s


class RainPoint2ZoneTimer(HomgarSubDevice):
    MODEL_CODES = [261]
    FRIENDLY_DESC = "2-Zone Water Timer"

    def _parse_device_specific_status_d_value(self, s):
        pass


class RainPointBridgeV2(HomgarHubDevice):
    MODEL_CODES = [289]
    FRIENDLY_DESC = "Rain Sensor Gateway V2"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connected = None
        self.battery_state = None
        self.raw_status = None
        self.raw_status_map = {}

    def get_device_status_ids(self):
        return ["connected", "state", "D01"]

    def set_device_status(self, api_obj):
        dev_id = api_obj["id"]
        val = api_obj.get("value")
        self.raw_status_map[dev_id] = val

        if dev_id == "connected":
            try:
                self.connected = int(val) == 1
            except (TypeError, ValueError):
                self.connected = None
        elif dev_id == "state":
            parts = [p.strip() for p in str(val).split(",") if p.strip()]
            if len(parts) >= 1:
                try:
                    battery_code = int(parts[0])
                    
                    if battery_code == 0:
                        self.battery_state = 100
                    elif battery_code == 1:
                        self.battery_state = 50
                    elif battery_code == 2:
                        self.battery_state = 10
                    else:
                        self.battery_state = None
                except ValueError:
                    self.battery_state = None
            if len(parts) >= 2:
                try:
                    self.rf_rssi = int(parts[1])
                except ValueError:
                    self.rf_rssi = None
        elif dev_id == "D01":
            self.raw_status = val

    def _parse_device_specific_status_d_value(self, s):
        pass


MODEL_CODE_MAPPING = {
    code: clazz
    for clazz in (
        RainPointDisplayHub,
        RainPointSoilMoistureSensor,
        RainPointRainSensor,
        RainPointAirSensor,
        RainPoint2ZoneTimer,
        RainPointBridgeV2,
    ) for code in clazz.MODEL_CODES
}
