from energy_inside.p1_meter import parse_p1_timestamp


def test_parse_p1_timestamp():
    # 260326193000 = 2026-03-26 19:30:00
    result = parse_p1_timestamp(260326193000)
    assert result == "2026-03-26 19:30:00"


def test_parse_p1_timestamp_leading_zero():
    # 260101080500 = 2026-01-01 08:05:00
    result = parse_p1_timestamp(260101080500)
    assert result == "2026-01-01 08:05:00"
