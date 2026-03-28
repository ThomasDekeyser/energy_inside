from energy_inside.p1_meter import parse_p1_timestamp, extract_reading


def test_parse_p1_timestamp():
    # 260326193000 = 2026-03-26 19:30:00
    result = parse_p1_timestamp(260326193000)
    assert result == "2026-03-26 19:30:00"


def test_parse_p1_timestamp_leading_zero():
    # 260101080500 = 2026-01-01 08:05:00
    result = parse_p1_timestamp(260101080500)
    assert result == "2026-01-01 08:05:00"


def test_extract_reading():
    api_response = {
        "wifi_ssid": "Proximus-Home-2DB8",
        "wifi_strength": 78,
        "smr_version": 50,
        "meter_model": "LGF5E360",
        "unique_id": "314C475A30353638363430383338",
        "active_tariff": 2,
        "total_power_import_kwh": 1594.842,
        "total_power_import_t1_kwh": 739.591,
        "total_power_import_t2_kwh": 855.251,
        "total_power_export_kwh": 2355.869,
        "total_power_export_t1_kwh": 1729.965,
        "total_power_export_t2_kwh": 625.904,
        "active_power_w": 77.000,
        "active_power_l1_w": -2039.000,
        "active_power_l2_w": 89.000,
        "active_power_l3_w": 2027.000,
        "active_voltage_l1_v": 243.300,
        "active_voltage_l2_v": 241.700,
        "active_voltage_l3_v": 241.000,
        "active_current_a": 18.240,
        "active_current_l1_a": 8.400,
        "active_current_l2_a": 0.870,
        "active_current_l3_a": 8.970,
        "active_power_average_w": 45.000,
        "montly_power_peak_w": 3560.000,
        "montly_power_peak_timestamp": 260326193000,
        "total_gas_m3": 809.162,
        "gas_timestamp": 260328103406,
        "gas_unique_id": "2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D",
        "external": [],
    }

    reading = extract_reading(api_response)

    assert reading["active_tariff"] == 2
    assert reading["total_power_import_kwh"] == 1594.842
    assert reading["active_power_l1_w"] == -2039.000
    assert reading["monthly_power_peak_w"] == 3560.000
    assert reading["monthly_power_peak_timestamp"] == "2026-03-26 19:30:00"
    assert reading["total_gas_m3"] == 809.162
    assert reading["gas_timestamp"] == "2026-03-28 10:34:06"
    # Should not contain wifi/meter metadata
    assert "wifi_ssid" not in reading
    assert "meter_model" not in reading
    assert "external" not in reading
    # Should contain a timestamp key
    assert "timestamp" in reading
