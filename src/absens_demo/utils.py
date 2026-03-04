from datetime import datetime, timedelta


def monthly_iso_start_end(start_date: str, months: int) -> list[tuple[str, str]]:
    start_datetime: datetime = datetime.strptime(start_date, "%Y-%m-%d")

    iso_start_end = [
        (
            (start_datetime + timedelta(days=i * months)).isoformat() + "Z",
            (start_datetime + timedelta(days=(i + 1) * months)).isoformat() + "Z",
        )
        for i in range(months)
    ]
    return iso_start_end
