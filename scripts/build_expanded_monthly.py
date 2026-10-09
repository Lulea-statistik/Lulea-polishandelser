from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data" / "events.csv"
DETAILS = ROOT / "data" / "summary_details_dedup.csv"
OUT = ROOT / "data" / "expanded_monthly_summary.csv"
OUT_STATS = ROOT / "data" / "expanded_summary_resolution_stats.csv"
OUT_QUIET = ROOT / "data" / "quiet_summaries_monthly.csv"

NO_NEW_EVENT_RE = re.compile(
    r"(?i)\b(?:"
    r"inget(?: särskilt)? att rapportera|"
    r"inget akut att rapportera|"
    r"inga (?:akuta |särskilda )?(?:händelser|ärenden)(?: att rapportera)?|"
    r"utan akuta händelser(?: att rapportera)?|"
    r"inga fler händelser värda att rapportera"
    r")\b"
)



# Conservative exclusion of stand-alone notices without a reported incident.
# Headline must itself identify a quiet/administrative bulletin; matching words
# only in the body is not sufficient because real incidents may be discussed too.
ADMIN_HEADLINE_RE = re.compile(
    r"(?i)^\s*(?:"
    r"ingen kommunikatör(?:\s+i\s+tjänst)?|"
    r"kommunikatör(?:en)?\s+(?:i\s+tjänst|saknas)|"
    r"tillfälligt obemannat|"
    r"en lugn (?:avslutning på |start på )?(?:natten|morgonen|kvällen|dagen)|"
    r"inget(?:\s+särskilt)?\s+att\s+rapportera|"
    r"inga\s+(?:akuta\s+)?händelser\s+att\s+rapportera|"
    r"det finns inga akuta händelser|"
    r"inga akuta händelser i länet|"
    r"lugn(?:t)?\s+(?:morgon|eftermiddag|kväll|natt|i länet)|"
    r"norrbotten,?\s+en fortsatt bra dag|"
    r"förtydligande av bemanning|"
    r"inga kommunikatörer i tjänst|"
    r"mediecentret obemannat|"
    r"ledningscentralen .*ej bemannad|"
    r"rlc är .*ej bemannad|"
    r"ingen\s+(?:media|medie|press|rlc-)?kommunikatör(?:\s+i\s+tjänst)?|"
    r"norrbotten,?\s+ingen\s+(?:media|medie|press|rlc-)?kommunikatör(?:\s+i\s+tjänst)?|"
    r"under kvällen(?:/natten)?\s+kommer vi inte ha någon kommunikatör"
    r")\b"
)
INCIDENT_IN_HEADLINE_RE = re.compile(
    r"(?i)\b(?:olycka|brand|rån|misshandel|inbrott|stöld|rattfylleri|"
    r"trafikkontroll|trafikbrott|larm|försvunnen|omhändertagen|"
    r"gripen|anhållen|skottlossning)\b"
)


def admin_non_event(row: pd.Series) -> bool:
    headline = str(row.get("headline", "") or "")
    title = str(row.get("type_original", "") or "")
    if INCIDENT_IN_HEADLINE_RE.search(headline):
        return False
    # Only remove high-confidence administrative type/headline combinations.
    administrative_type = title.casefold().strip() in {"övrigt", "tillfälligt obemannat"}
    if not administrative_type or not ADMIN_HEADLINE_RE.search(headline):
        return False
    # Exception: a concrete report in the body must not be silently removed.
    body = str(row.get("content", "") or "")
    incident_lines = re.search(
        r"(?im)^\s*(?:kl(?:ockan)?\.?\s*)?\d{1,2}[.:]\d{2}\s+"
        r".*(?:polis|patrull|olycka|brand|stöld|misstänk|larm|grip)",
        body,
    )
    return not bool(incident_lines)

def truthy(series: pd.Series) -> pd.Series:
    return series.astype(str).str.casefold().isin(["true", "1"])


def summary_text(row: pd.Series) -> str:
    return " ".join(
        str(row.get(col, "") or "")
        for col in ("headline", "description", "content")
    )


def quiet_bucket(value: str) -> str:
    s = str(value or "").casefold()
    if "kväll" in s and "natt" in s:
        return "Kväll/natt"
    if "natt" in s:
        return "Natt"
    if "förmiddag" in s:
        return "Förmiddag"
    if "eftermiddag" in s:
        return "Eftermiddag"
    if "kväll" in s:
        return "Kväll"
    if "dag" in s:
        return "Dag"
    if "helg" in s:
        return "Helg"
    return "Övrig sammanfattning"


def main() -> None:
    events = pd.read_csv(EVENTS, dtype={"event_id": "string"}, low_memory=False)
    details = pd.read_csv(DETAILS, dtype={"parent_event_id": "string"}, low_memory=False)

    is_summary = truthy(events.get("is_summary", pd.Series(False, index=events.index)))

    # Råposter bevaras, men rena informationsnotiser räknas inte som händelser.
    ordinary = events[~is_summary].copy()
    ordinary["excluded_admin_non_event"] = ordinary.apply(admin_non_event, axis=1)
    excluded_admin = ordinary[ordinary["excluded_admin_non_event"]].copy()
    ordinary = ordinary[~ordinary["excluded_admin_non_event"]].copy()
    excluded_admin[["event_id", "date", "type_original", "headline", "geography_group"]].to_csv(
        ROOT / "data" / "excluded_administrative_notices.csv", index=False, encoding="utf-8"
    )
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
    unresolved["explicit_no_new_event"] = unresolved.apply(
        lambda r: bool(NO_NEW_EVENT_RE.search(summary_text(r))), axis=1
    )
    quiet = unresolved[unresolved["explicit_no_new_event"]].copy()
    quiet["quiet_bucket"] = quiet["type_original"].map(quiet_bucket)
    quiet_monthly = (
        quiet.groupby(["year", "month", "geography_group", "quiet_bucket"], dropna=False)
        .size().reset_index(name="event_count")
        .sort_values(["year", "month", "geography_group", "quiet_bucket"])
    )
    quiet_monthly.to_csv(OUT_QUIET, index=False, encoding="utf-8")

    unresolved_keep = unresolved[~unresolved["explicit_no_new_event"]].copy()
    unresolved_rows = unresolved_keep[["year", "month", "geography_group"]].copy()
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
    no_new_event_total = int(unresolved["explicit_no_new_event"].sum())
    unresolved_kept_total = len(unresolved_keep)
    parsed_total = summary_total - unresolved_total

    pd.DataFrame([
        ("summaries_total", summary_total),
        ("summaries_expanded", parsed_total),
        ("summaries_explicit_no_new_event", no_new_event_total),
        ("summaries_unresolved_kept", unresolved_kept_total),
        ("extra_subevents", len(extra_rows)),
        ("ordinary_administrative_excluded", len(excluded_admin)),
    ], columns=["metric", "value"]).to_csv(OUT_STATS, index=False, encoding="utf-8")

    print(
        f"expanded_rows={len(expanded)} summaries_total={summary_total} "
        f"summaries_expanded={parsed_total} summaries_no_new_event={no_new_event_total} "
        f"summaries_unresolved_kept={unresolved_kept_total} extra_subevents={len(extra_rows)} "
        f"ordinary_administrative_excluded={len(excluded_admin)}"
    )


if __name__ == "__main__":
    main()
