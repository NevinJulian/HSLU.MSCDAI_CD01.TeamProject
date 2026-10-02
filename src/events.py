"""Events for the time charts, see issue 11."""

import pandas as pd

EVENTS = [
    ("2021-01-01", "2021-05-31", "lockdown, restaurants closed", "restaurants, holidays"),
    ("2021-09-13", "2022-02-16", "covid certificate indoors", "restaurants, entertainment"),
    ("2021-04-14", None, "bitcoin high", "crypto"),
    ("2021-11-10", None, "bitcoin high", "crypto"),
    ("2022-02-24", None, "Ukraine war, fuel and food prices", "fuel, groceries"),
    ("2022-05-09", None, "Terra/Luna collapse", "crypto"),
    ("2022-06-16", None, "SNB first hike", "banks"),
    ("2022-09-22", None, "SNB rate positive", "banks, savings"),
    ("2022-11-11", None, "FTX collapse", "crypto"),
    ("2023-03-19", None, "Credit Suisse rescue", "banks"),
]


def events(affects: str | None = None) -> pd.DataFrame:
    df = pd.DataFrame(EVENTS, columns=["start", "end", "event", "affects"])
    df["start"] = pd.to_datetime(df["start"])
    df["end"] = pd.to_datetime(df["end"])
    if affects:
        df = df[df["affects"].str.contains(affects)]
    return df.reset_index(drop=True)
