from energy_inside.sql import build_insert


def test_build_insert():
    reading = {
        "timestamp": "2026-03-28 10:45:00",
        "active_tariff": 2,
        "total_power_import_kwh": 1594.842,
        "active_power_l1_w": -2039.0,
        "monthly_power_peak_timestamp": "2026-03-26 19:30:00",
    }

    sql = build_insert(reading)

    assert sql.startswith("REPLACE INTO readings")
    assert "'2026-03-28 10:45:00'" in sql
    assert "2" in sql
    assert "1594.842" in sql
    assert "-2039.0" in sql
    assert "'2026-03-26 19:30:00'" in sql


def test_build_insert_escapes_strings():
    reading = {
        "timestamp": "2026-03-28 10:45:00",
        "active_tariff": 1,
    }
    sql = build_insert(reading)
    assert "REPLACE INTO readings" in sql
    assert "'2026-03-28 10:45:00'" in sql
