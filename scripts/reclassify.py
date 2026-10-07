from __future__ import annotations

import pandas as pd

from common import EVENTS_CSV, infer_municipality_detail, geography_group, write_monthly_summary


def main() -> None:
    df = pd.read_csv(EVENTS_CSV, dtype={"event_id": "string"})
    before = df["geography_group"].value_counts(dropna=False).to_dict()

    details = []
    sources = df["municipality_source"].fillna("") if "municipality_source" in df.columns else pd.Series([""] * len(df))
    for m, t, l, source in zip(
        df["municipality"].fillna(""),
        df["title_location"].fillna(""),
        df["location_string"].fillna(""),
        sources,
    ):
        existing = str(m).strip()
        source = str(source).strip()

        # Re-evaluate earlier place-name assignments with the current stricter rules.
        if source == "lulea_place_name":
            details.append(infer_municipality_detail("", t, l))
        elif existing:
            details.append((existing, source or "existing_pre_source"))
        else:
            details.append(infer_municipality_detail("", t, l))

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
    print("lulea_rows=", int((df["geography_group"] == "Luleå kommun").sum()))
    print("municipality_source=", df["municipality_source"].value_counts(dropna=False).to_dict())


if __name__ == "__main__":
    main()
