"""Daily observation coverage and weekday/time-block aggregates.

An unknown time is never assigned from the publication timestamp.
"""
from pathlib import Path
import pandas as pd
import re

ROOT = Path(__file__).resolve().parents[1]
BLOCKS = ("Eftermiddag", "Kväll", "Kväll/natt", "Natt")
OUT = ROOT / "data" / "weekday_period_observations.csv"
CALENDAR_OUT = ROOT / "data" / "weekday_period_calendar.csv"

def valid_dates(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.loc[df["date"].notna()].copy()

def block_from_time(value):
    text = str(value or "").strip().replace(".", ":")
    if ":" not in text:
        return ""
    try:
        h, minute = (int(v) for v in text.split(":", 1))
    except ValueError:
        return ""
    if h > 23 or minute > 59:
        return ""
    if 12 <= h < 18:
        return "Eftermiddag"
    if 18 <= h < 22:
        return "Kväll"
    if h >= 22 or h < 6:
        return "Natt"
    return ""

def main():
    events = pd.read_csv(ROOT / "data" / "events.csv", low_memory=False, dtype={"event_id": "string"})
    details = pd.read_csv(ROOT / "data" / "summary_details_dedup.csv", low_memory=False, dtype={"parent_event_id": "string"})
    stats = pd.read_csv(ROOT / "data" / "excluded_administrative_notices.csv", low_memory=False, dtype={"event_id": "string"})
    is_summary = events["is_summary"].astype(str).str.lower().isin(("true", "1"))
    ordinary = events.loc[~is_summary & ~events["event_id"].astype(str).isin(stats["event_id"].astype(str))].copy()
    included = details.loc[details["include_as_extra"].astype(str).str.lower().isin(("true","1"))].copy()
    parsed_ids = set(details["parent_event_id"].dropna().astype(str))
    unresolved = events.loc[is_summary & ~events["event_id"].astype(str).isin(parsed_ids)].copy()

    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_expanded_monthly import NO_NEW_EVENT_RE, summary_text, quiet_bucket
    quiet_mask = unresolved.apply(lambda r: bool(NO_NEW_EVENT_RE.search(summary_text(r))), axis=1)
    quiet = unresolved.loc[quiet_mask].copy()
    # Independent quiet observations: also retain explicitly quiet summaries
    # which have identifiable subevents. Do not infer quietness from silence.
    all_summaries = events.loc[is_summary].copy()
    # Only classify explicit quiet language in a summary headline as quiet.
    # A vague lack of reports is not a reliable zero-event observation.
    QUIET_HEADLINE = re.compile(r"(?i)\\b(?:lugn(?:t|a)?\\s+(?:eftermiddag|kväll|natt)|(?:eftermiddagen|kvällen|natten)\\s+(?:har\\s+varit\\s+)?lugn|inga\\s+(?:akuta\\s+)?händelser|inget\\s+(?:särskilt\\s+)?att\\s+rapportera)\\b")
    quiet_all = all_summaries.loc[all_summaries.apply(
        lambda r: bool(NO_NEW_EVENT_RE.search(summary_text(r)) or QUIET_HEADLINE.search(str(r.get("headline", "") or ""))),
        axis=1
    )].copy()
    # Keep the original narrow quiet series for the observation chart, but
    # use all explicitly quiet summaries for the calendar analysis.
    unresolved = unresolved.loc[~quiet_mask]

    datasets = []
    for source, frame, category, period_field in [
        ("vanlig", ordinary, "Händelse", ""),
        ("extra", included, "Händelse", "time"),
        ("oupplost", unresolved, "Händelse", ""),
        ("lugn", quiet, "Icke-händelse", "type_original")
    ]:
        part = valid_dates(frame)
        part["kind"] = category
        part["period"] = (part[period_field].map(block_from_time) if source == "extra"
                          else part[period_field].map(quiet_bucket) if source == "lugn"
                          else "")
        part.loc[~part["period"].isin(BLOCKS), "period"] = ""
        part["event_type"] = part["event_type_extracted"] if source == "extra" else (
            part["type_original"] if source == "vanlig" else
            "Sammanfattning, ej uppdelad" if source == "oupplost" else "Lugn sammanfattning"
        )
        datasets.append(part[["date", "geography_group", "kind", "period", "event_type"]])
    combined = pd.concat(datasets, ignore_index=True)
    combined["year"] = combined["date"].dt.year
    combined["weekday"] = combined["date"].dt.weekday
    combined["time_known"] = combined["period"].ne("").astype(int)
    combined["event_count"] = 1
    result = combined.groupby(
        ["year", "geography_group", "kind", "period", "event_type", "weekday", "time_known"],
        dropna=False
    )["event_count"].sum().reset_index()
    result.to_csv(OUT, index=False, encoding="utf-8")
    quiet_cal = valid_dates(quiet_all)
    quiet_cal["period"] = quiet_cal["type_original"].map(quiet_bucket)
    quiet_cal = quiet_cal.loc[quiet_cal["period"].isin(BLOCKS)]
    quiet_cal["kind"] = "Icke-händelse"
    # Do not duplicate ordinary and extracted events in the daily status grid.
    calendar_events = pd.concat([valid_dates(ordinary), valid_dates(included)], ignore_index=True)
    calendar_events["period"] = ""
    ordinary_n = len(valid_dates(ordinary))
    calendar_events.loc[calendar_events.index >= ordinary_n, "period"] = (
        calendar_events.loc[calendar_events.index >= ordinary_n, "time"].map(block_from_time)
    )
    calendar_events = calendar_events.loc[calendar_events["period"].isin(BLOCKS)].copy()
    calendar_events["kind"] = "Händelse"
    cal = pd.concat([
        calendar_events[["date", "geography_group", "period", "kind"]],
        quiet_cal[["date", "geography_group", "period", "kind"]]
    ], ignore_index=True)
    # A single date and period can contain many reports, but remains one day.
    cal = cal.groupby(["date", "geography_group", "period", "kind"]).size().unstack(fill_value=0).reset_index()
    for kind in ("Händelse", "Icke-händelse"):
        if kind not in cal.columns:
            cal[kind] = 0
    cal["year"] = cal["date"].dt.year
    cal["weekday"] = cal["date"].dt.weekday
    cal["status"] = cal.apply(lambda r: (
        "Båda" if r["Händelse"] and r["Icke-händelse"] else
        "Händelse" if r["Händelse"] else "Lugn"
    ), axis=1)
    cal.rename(columns={"Händelse": "event_count", "Icke-händelse": "quiet_count"}, inplace=True)
    cal[["date", "year", "weekday", "geography_group", "period", "event_count", "quiet_count", "status"]].to_csv(
        CALENDAR_OUT, index=False, encoding="utf-8"
    )
    print(f"calendar_day_periods={len(cal)}")
    print(f"dated_observations={len(combined)} assigned_period={int(combined['time_known'].sum())}")

if __name__ == "__main__":
    main()
