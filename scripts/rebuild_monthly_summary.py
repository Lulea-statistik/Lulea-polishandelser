from __future__ import annotations

from pathlib import Path
import pandas as pd

from common import write_monthly_summary

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data" / "events.csv"


def main() -> None:
    if not EVENTS.exists() or EVENTS.stat().st_size == 0:
        raise SystemExit("data/events.csv saknas eller är tom")
    df = pd.read_csv(EVENTS, dtype={"event_id": "string"}, low_memory=False)
    write_monthly_summary(df)
    pairs = df["geography_group"].fillna("").astype(str).str.contains(" kommun / ", regex=False).sum()
    print(f"rebuilt_monthly_from_events rows={len(df)} pair_rows_in_events={pairs}")


if __name__ == "__main__":
    main()
