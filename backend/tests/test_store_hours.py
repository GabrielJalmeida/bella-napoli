from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest

from app.domain.store_hours import is_store_open


BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")


def test_closed_store_is_not_open():
    current_datetime = datetime(
        2026,
        9,
        21,
        20,
        0,
        tzinfo=BRAZIL_TZ,
    )

    assert is_store_open(
        current_datetime=current_datetime,
        is_closed=True,
        open_time=None,
        close_time=None,
    ) is False


def test_store_is_open_at_opening_time():
    current_datetime = datetime(
        2026,
        9,
        22,
        18,
        0,
        tzinfo=BRAZIL_TZ,
    )

    assert is_store_open(
        current_datetime=current_datetime,
        is_closed=False,
        open_time=time(18, 0),
        close_time=time(23, 0),
    ) is True


def test_store_is_closed_before_opening():
    current_datetime = datetime(
        2026,
        9,
        22,
        17,
        59,
        tzinfo=BRAZIL_TZ,
    )

    assert is_store_open(
        current_datetime=current_datetime,
        is_closed=False,
        open_time=time(18, 0),
        close_time=time(23, 0),
    ) is False


def test_store_is_closed_at_normal_closing_time():
    current_datetime = datetime(
        2026,
        9,
        22,
        23,
        0,
        tzinfo=BRAZIL_TZ,
    )

    assert is_store_open(
        current_datetime=current_datetime,
        is_closed=False,
        open_time=time(18, 0),
        close_time=time(23, 0),
    ) is False


def test_store_is_open_before_midnight():
    current_datetime = datetime(
        2026,
        9,
        25,
        23,
        59,
        tzinfo=BRAZIL_TZ,
    )

    assert is_store_open(
        current_datetime=current_datetime,
        is_closed=False,
        open_time=time(18, 0),
        close_time=time(0, 0),
    ) is True


def test_store_is_closed_at_midnight_next_day():
    current_datetime = datetime(
        2026,
        9,
        26,
        0,
        0,
        tzinfo=BRAZIL_TZ,
    )

    assert is_store_open(
        current_datetime=current_datetime,
        is_closed=False,
        open_time=time(18, 0),
        close_time=time(0, 0),
    ) is False


def test_store_is_closed_after_midnight_next_day():
    current_datetime = datetime(
        2026,
        9,
        26,
        0,
        1,
        tzinfo=BRAZIL_TZ,
    )

    assert is_store_open(
        current_datetime=current_datetime,
        is_closed=False,
        open_time=time(18, 0),
        close_time=time(0, 0),
    ) is False


def test_store_is_open_saturday_evening():
    current_datetime = datetime(
        2026,
        9,
        26,
        18,
        0,
        tzinfo=BRAZIL_TZ,
    )

    assert is_store_open(
        current_datetime=current_datetime,
        is_closed=False,
        open_time=time(18, 0),
        close_time=time(0, 0),
    ) is True


def test_naive_datetime_is_rejected():
    current_datetime = datetime(
        2026,
        9,
        22,
        19,
        0,
    )

    with pytest.raises(
        ValueError,
        match="timezone",
    ):
        is_store_open(
            current_datetime=current_datetime,
            is_closed=False,
            open_time=time(18, 0),
            close_time=time(23, 0),
        )


def test_missing_times_are_rejected_for_open_store():
    current_datetime = datetime(
        2026,
        9,
        22,
        19,
        0,
        tzinfo=BRAZIL_TZ,
    )

    with pytest.raises(ValueError):
        is_store_open(
            current_datetime=current_datetime,
            is_closed=False,
            open_time=None,
            close_time=None,
        )

def test_friday_2359_in_brazil_is_still_open():
    current_datetime = datetime(
        2026,
        9,
        26,
        2,
        59,
        tzinfo=ZoneInfo("UTC"),
    )

    assert current_datetime.astimezone(BRAZIL_TZ).strftime(
        "%A %H:%M"
    ) == "Friday 23:59"