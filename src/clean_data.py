"""Write the cleaned tables to data/processed/ as CSV.

    python src/clean_data.py

The cleaning itself lives in src/data.py (loaders) and src/features.py, this
script only calls them. Notebooks import the loaders directly and do not need
the CSVs. See docs/data_preparation.md for what is cleaned and why.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import build_processed  # noqa: E402


def main() -> None:
    for path in build_processed():
        print(f"written {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
