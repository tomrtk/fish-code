"""Unit test for date parsing."""
from datetime import datetime


from core.model import parse_str_to_date


def test_parse_str_to_date_no_offset():
    """Test parse str to date with no offset."""
    date = datetime(2020, 3, 28, 12, 30, 10)

    date_str = "ramdom text [2020-03-28_12-30-10] other string"
    assert date == parse_str_to_date(date_str)

    date_str = "[2020-03-28_12-30-10]"
    assert date == parse_str_to_date(date_str)

    # missing []
    date_str = "2020-03-28_12-30-10"
    assert parse_str_to_date(date_str) is None

    # invalid month
    date_str = "[2020-13-28_12-30-10]"
    assert parse_str_to_date(date_str) is None

    # invalid delimiter
    date_str = "[2020-12 28_12-30-10]"
    assert parse_str_to_date(date_str) is None


def test_parse_str_to_date_with_offset():
    """Test parse str to date with offset."""
    date = datetime(2020, 3, 28, 13, 0, 10)

    date_str = "ramdom text [2020-03-28_12-30-10]-001 other string"
    assert date == parse_str_to_date(date_str)

    date_str = "[2020-03-28_12-30-10]-001"
    assert date == parse_str_to_date(date_str)

    # invalid month
    date_str = "[2020-13-28_12-30-10]-001"
    assert parse_str_to_date(date_str) is None

    # invalid delimiter
    date_str = "[2020-12 28_12-30-10]-001"
    assert parse_str_to_date(date_str) is None
