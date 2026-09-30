import pandas as pd

from src.events import events


def test_events_table():
    e = events()
    assert len(e) >= 8
    assert pd.api.types.is_datetime64_any_dtype(e["start"])
    assert (e["start"] >= "2021-01-01").all() and (e["start"] <= "2023-12-31").all()
    assert len(events("crypto")) == 4
