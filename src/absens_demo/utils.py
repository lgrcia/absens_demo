from datetime import datetime

from dateutil.relativedelta import relativedelta


def monthly_iso_start_end(start_date: str, months: int) -> list[tuple[str, str]]:
    """Generate a list of (start, end) ISO 8601 datetime pairs, one per month.

    Args:
        start_date (str): Start date in YYYY-MM-DD format.
        months (int): Number of monthly intervals to generate.

    Returns:
        list[tuple[str, str]]: List of (start_iso, end_iso) pairs, each covering
            an exact calendar month window offset from start_date.
    """
    start_datetime: datetime = datetime.strptime(start_date, "%Y-%m-%d")

    iso_start_end = [
        (
            (start_datetime + relativedelta(months=i)).isoformat() + "Z",
            (start_datetime + relativedelta(months=i + 1)).isoformat() + "Z",
        )
        for i in range(months)
    ]
    return iso_start_end
