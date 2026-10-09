from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data" / "events.csv"
DETAILS = ROOT / "data" / "summary_details_dedup.csv"
OUT = ROOT / "data" / "expanded_monthly_summary.csv"


def truthy(series: pd.Series) -> pd.Series:
    return series.astype(str).str.casefold().isin(["true", "1"])


def main() -> None:
    events = pd.read_csv(EVENTS, dtype={"event_id": "string"}, low_memory=False)
    details = pd.read_csv(DETAILS, dtype={"parent_event_id": "string"}, low_memory=False)

    is_summary = truthy(events.get("is_summary", pd.Series(False, index=events.index)))

    # Vanliga publicerade poster behålls oförändrade.
    ordinary = events[~is_summary].copy()
    ordinary_rows = ordinary[["year", "month", "geography_group", "type_original"]].copy()
    ordinary_rows = ordinary_rows.rename(columns={"type_original": "event_type"})

    # En sammanfattning räknas som uppdelad så snart parsern har identifierat
    # minst en konkret underhändelse i den, oavsett om just den underhändelsen
    # senare bedöms vara en dublett av en vanlig polisnotis.
    parsed_parent_ids = set(details["parent_event_id"].dropna().astype("string"))

    # Endast underhändelser som passerat den konservativa dublettkontrollen
    # läggs till i den expanderade serien.
    include_extra = truthy(details.get("include_as_extra", pd.Series(False, index=details.index)))
    extra = details[include_extra].copy()
    extra_rows = extra[["year", "month", "geography_group", "event_type_extracted"]].copy()
    extra_rows = extra_rows.rename(columns={"event_type_extracted": "event_type"})

    # Sammanfattningar där parsern inte hittat någon konkret underhändelse
    # behålls, men med en tydlig restkategori i stället för flera olika
    # "Sammanfattning natt/dag/..."-etiketter.
    unresolved = events[is_summary & ~events["event_id"].astype("string").isin(parsed_parent_ids)].copy()
    unresolved_rows = unresolved[["year", "month", "geography_group"]].copy()
    unresolved_rows["event_type"] = "Sammanfattning, ej uppdelad"

    expanded = pd.concat([ordinary_rows, extra_rows, unresolved_rows], ignore_index=True)
    expanded["year"] = pd.to_numeric(expanded["year"], errors="coerce")
    expanded["month"] = pd.to_numeric(expanded["month"], errors="coerce")
    expanded = expanded.dropna(subset=["year", "month"])
    expanded["year"] = expanded["year"].astype(int)
    expanded["month"] = expanded["month"].astype(int)

    monthly = (
        expanded.groupby(["year", "month", "geography_group", "event_type"], dropna=False)
        .size().reset_index(name="event_count")
        .sort_values(
            ["year", "month", "geography_group", "event_count", "event_type"],
            ascending=[True, True, True, False, True],
        )
    )
    monthly.to_csv(OUT, index=False, encoding="utf-8")

    summary_total = int(is_summary.sum())
    unresolved_total = len(unresolved)
    parsed_total = summary_total - unresolved_total
    print(
        f"expanded_rows={len(expanded)} summaries_total={summary_total} "
        f"summaries_expanded={parsed_total} summaries_unresolved={unresolved_total} "
        f"extra_subevents={len(extra_rows)}"
    )


if __name__ == "__main__":
    main()
