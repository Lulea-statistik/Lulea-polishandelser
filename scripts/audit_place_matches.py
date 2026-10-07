from __future__ import annotations

import pandas as pd

from common import EVENTS_CSV, infer_lulea_place

OUT = EVENTS_CSV.parent / "lulea_place_audit.csv"


def main() -> None:
    df = pd.read_csv(EVENTS_CSV, dtype={"event_id": "string"})
    if "municipality_source" not in df.columns:
        raise RuntimeError("municipality_source saknas i events.csv")

    x = df[df["municipality_source"].fillna("") == "lulea_place_name"].copy()
    x["matched_place"] = [
        infer_lulea_place(t, l)
        for t, l in zip(
            x["title_location"].fillna(""),
            x["location_string"].fillna(""),
        )
    ]

    unresolved = int((x["matched_place"] == "").sum())
    if unresolved:
        print(f"warning_unresolved_matched_place={unresolved}")

    rows = []
    for place, g in x[x["matched_place"] != ""].groupby("matched_place"):
        examples = (
            g["headline"].fillna("").astype(str)
            .replace("", pd.NA).dropna().drop_duplicates().head(3).tolist()
        )
        title_locations = (
            g["title_location"].fillna("").astype(str)
            .replace("", pd.NA).dropna().drop_duplicates().head(3).tolist()
        )
        location_strings = (
            g["location_string"].fillna("").astype(str)
            .replace("", pd.NA).dropna().drop_duplicates().head(3).tolist()
        )
        rows.append({
            "matched_place": place,
            "event_count": len(g),
            "share_of_place_matches_pct": round(len(g) / len(x) * 100, 2) if len(x) else 0,
            "title_location_1": title_locations[0] if len(title_locations) > 0 else "",
            "title_location_2": title_locations[1] if len(title_locations) > 1 else "",
            "location_string_1": location_strings[0] if len(location_strings) > 0 else "",
            "location_string_2": location_strings[1] if len(location_strings) > 1 else "",
            "example_1": examples[0] if len(examples) > 0 else "",
            "example_2": examples[1] if len(examples) > 1 else "",
            "example_3": examples[2] if len(examples) > 2 else "",
        })

    out = pd.DataFrame(rows).sort_values(
        ["event_count", "matched_place"], ascending=[False, True]
    )
    out.to_csv(OUT, index=False, encoding="utf-8")

    print(f"place_matches_total={len(x)}")
    print("top_places=")
    print(out.head(25).to_string(index=False))


if __name__ == "__main__":
    main()
