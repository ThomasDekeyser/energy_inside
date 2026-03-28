from datetime import datetime


def parse_p1_timestamp(raw: int) -> str:
    """Parse P1 meter timestamp format YYMMDDHHmmss into 'YYYY-MM-DD HH:MM:SS'."""
    s = str(raw)
    dt = datetime.strptime(s, "%y%m%d%H%M%S")
    return dt.strftime("%Y-%m-%d %H:%M:%S")
