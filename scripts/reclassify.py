from __future__ import annotations

import pandas as pd

from common import EVENTS_CSV, infer_municipality_detail, geography_group, write_monthly_summary


def main() -> None:
    df = pd.read_csv(EVENTS_CSV, dtype={"event_id": "string"})
    before = df["geography_group"].value_counts(dropna=False).to_dict()

    details = [
        infer_municipality_detail(m, t, l)
        for m, t, l in zip(
            df["municipality"].fillna(""),
            df["title_location"].fillna(""),
            df["location_string"].fillna(""),
        )
    ]
    df["municipality"] = [x[0] for x in details]
    df["municipality_source"] = [x[1] for x in details]
    df["geography_group"] = [
        geography_group(m, a)
        for m, a in zip(
            df["municipality"].fillna(""),
            df["administrative_area_level_1"].fillna(""),
        )
    ]

    df.to_csv(EVENTS_CSV, index=False, encoding="utf-8")
    write_monthly_summary(df)

    after = df["geography_group"].value_counts(dropna=False).to_dict()
    print("before=", before)
    print("after=", after)
    print("lulea_rows=", int((df["geography_group"] == "Luleå kommun").sum()))\n    print("municipality_source=", df["municipality_source"].value_counts(dropna=False).to_dict())


if __name__ == "__main__":
    main()
