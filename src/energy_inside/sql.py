COLUMNS = [
    "timestamp",
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
    "monthly_power_peak_w",
    "monthly_power_peak_timestamp",
    "total_gas_m3",
    "gas_timestamp",
]


def _format_value(value) -> str:
    """Format a value for SQL insertion."""
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    return str(value)


def build_insert(reading: dict) -> str:
    """Build a REPLACE INTO SQL statement from a reading dict."""
    cols = [c for c in COLUMNS if c in reading]
    vals = [_format_value(reading[c]) for c in cols]
    columns_str = ", ".join(cols)
    values_str = ", ".join(vals)
    return f"REPLACE INTO readings ({columns_str}) VALUES ({values_str})"
