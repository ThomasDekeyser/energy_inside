from datetime import datetime, timezone


ENERGY_FIELDS = [
    "active_tariff",
    "total_power_import_kwh",
    "total_power_import_t1_kwh",
    "total_power_import_t2_kwh",
    "total_power_export_kwh",
    "total_power_export_t1_kwh",
    "total_power_export_t2_kwh",
    "active_power_w",
    "active_power_l1_w",
    "active_power_l2_w",
    "active_power_l3_w",
    "active_voltage_l1_v",
    "active_voltage_l2_v",
    "active_voltage_l3_v",
    "active_current_a",
    "active_current_l1_a",
    "active_current_l2_a",
    "active_current_l3_a",
    "active_power_average_w",
    "total_gas_m3",
]


def parse_p1_timestamp(raw: int) -> str:
    """Parse P1 meter timestamp format YYMMDDHHmmss into 'YYYY-MM-DD HH:MM:SS'."""
    s = str(raw)
    dt = datetime.strptime(s, "%y%m%d%H%M%S")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def extract_reading(data: dict) -> dict:
    """Extract energy fields from P1 meter API response."""
    reading = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }

    for field in ENERGY_FIELDS:
        reading[field] = data[field]

    # Fields with typo in API + rename
    reading["monthly_power_peak_w"] = data["montly_power_peak_w"]
    reading["monthly_power_peak_timestamp"] = parse_p1_timestamp(
        data["montly_power_peak_timestamp"]
    )
    reading["gas_timestamp"] = parse_p1_timestamp(data["gas_timestamp"])

    return reading
