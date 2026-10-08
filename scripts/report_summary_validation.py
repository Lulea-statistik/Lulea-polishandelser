from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "summary_validation_sample.csv"
DETAILS = ROOT / "data" / "summary_details.csv"
DEDUP = ROOT / "data" / "summary_details_dedup.csv"
OUT = ROOT / "data" / "summary_validation_report.csv"
OUT_MD = ROOT / "data" / "summary_validation_report.md"


def wilson(success: float, total: float, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return (float("nan"), float("nan"))
    p = success / total
    den = 1 + z * z / total
    center = (p + z * z / (2 * total)) / den
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / den
    return max(0.0, center - half), min(1.0, center + half)


def num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def fmt_pct(x: float) -> str:
    return "saknas" if pd.isna(x) else f"{100*x:.1f} %"


def bootstrap_ratio(df: pd.DataFrame, num_col: str, den_col: str, n: int = 10000, seed: int = 20261008) -> tuple[float, float]:
    if df.empty:
        return (float("nan"), float("nan"))
    a = df[num_col].to_numpy(dtype=float)
    b = df[den_col].to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    vals = []
    m = len(df)
    for _ in range(n):
        idx = rng.integers(0, m, size=m)
        den = b[idx].sum()
        if den > 0:
            vals.append(a[idx].sum() / den)
    if not vals:
        return (float("nan"), float("nan"))
    lo, hi = np.quantile(np.asarray(vals), [0.025, 0.975])
    return float(lo), float(hi)


def main() -> None:
    if not SAMPLE.exists():
        raise SystemExit("data/summary_validation_sample.csv saknas")

    s = pd.read_csv(SAMPLE, dtype={"event_id": "string"}, low_memory=False)
    needed = [
        "manual_count", "manual_lulea_count", "parser_correct_count",
        "parser_false_positive_count", "parser_missed_count",
        "extracted_count", "parser_lulea_count",
    ]
    for c in needed:
        if c not in s.columns:
            s[c] = pd.NA
        s[c] = num(s[c])

    # En rad räknas som färdig global validering först när de tre centrala
    # manuella fälten är ifyllda.
    checked = s[
        s[["parser_correct_count", "parser_false_positive_count", "parser_missed_count"]]
        .notna().all(axis=1)
    ].copy()

    correct = checked["parser_correct_count"].sum()
    false_pos = checked["parser_false_positive_count"].sum()
    missed = checked["parser_missed_count"].sum()

    precision_den = correct + false_pos
    recall_den = correct + missed
    precision = correct / precision_den if precision_den else float("nan")
    recall = correct / recall_den if recall_den else float("nan")
    p_lo, p_hi = wilson(correct, precision_den)
    r_lo, r_hi = wilson(correct, recall_den)

    # Om parsern hittar E poster gäller ungefär sann mängd E * precision / recall.
    # Konservativt 95%-intervall kombinerar nedre precision med övre recall
    # respektive övre precision med nedre recall.
    factor = precision / recall if recall and not pd.isna(precision) else float("nan")
    factor_lo = p_lo / r_hi if r_hi and not pd.isna(p_lo) else float("nan")
    factor_hi = p_hi / r_lo if r_lo and not pd.isna(p_hi) else float("nan")

    # Bootstrap på sammanfattningsnivå bevarar klustringen inom varje
    # sammanfattning och är därför bättre som praktiskt osäkerhetsintervall.
    checked["manual_events_for_ratio"] = checked["parser_correct_count"] + checked["parser_missed_count"]
    checked["parser_events_for_ratio"] = checked["parser_correct_count"] + checked["parser_false_positive_count"]
    boot_lo, boot_hi = bootstrap_ratio(
        checked, "manual_events_for_ratio", "parser_events_for_ratio"
    )

    total_extracted = float("nan")
    total_lulea = float("nan")
    if DETAILS.exists():
        d = pd.read_csv(DETAILS, low_memory=False)
        total_extracted = float(len(d))
        total_lulea = float((d.get("municipality", pd.Series("", index=d.index)).fillna("") == "Luleå").sum())

    # Extra efter konservativ deduplicering mot vanliga polisnotiser är det
    # mått som används för linjen "Inkl. sammanfattningar".
    extra_total = float("nan")
    extra_lulea = float("nan")
    if DEDUP.exists():
        d = pd.read_csv(DEDUP, low_memory=False)
        inc = d.get("include_as_extra", pd.Series(False, index=d.index)).astype(str).str.casefold().isin(["true", "1"])
        extra_total = float(inc.sum())
        extra_lulea = float((inc & (d.get("municipality", pd.Series("", index=d.index)).fillna("") == "Luleå")).sum())

    # Separat Luleå-kvot kan användas när manual_lulea_count finns. Den kräver
    # inte att typerna är perfekta, bara att antalet Luleå-underhändelser räknats.
    lchk = s[s["manual_lulea_count"].notna() & s["parser_lulea_count"].notna()].copy()
    manual_lulea = lchk["manual_lulea_count"].sum()
    parser_lulea = lchk["parser_lulea_count"].sum()
    lulea_factor = manual_lulea / parser_lulea if parser_lulea else float("nan")
    lulea_boot_lo, lulea_boot_hi = bootstrap_ratio(
        lchk, "manual_lulea_count", "parser_lulea_count"
    )

    lulea_extracted_est = total_lulea * lulea_factor if not pd.isna(total_lulea) and not pd.isna(lulea_factor) else float("nan")
    lulea_extracted_low = total_lulea * lulea_boot_lo if not pd.isna(total_lulea) and not pd.isna(lulea_boot_lo) else float("nan")
    lulea_extracted_high = total_lulea * lulea_boot_hi if not pd.isna(total_lulea) and not pd.isna(lulea_boot_hi) else float("nan")
    lulea_extra_est = extra_lulea * lulea_factor if not pd.isna(extra_lulea) and not pd.isna(lulea_factor) else float("nan")
    lulea_extra_low = extra_lulea * lulea_boot_lo if not pd.isna(extra_lulea) and not pd.isna(lulea_boot_lo) else float("nan")
    lulea_extra_high = extra_lulea * lulea_boot_hi if not pd.isna(extra_lulea) and not pd.isna(lulea_boot_hi) else float("nan")

    rows = [
        ("sample_rows", len(s)),
        ("checked_rows", len(checked)),
        ("correct", correct),
        ("false_positive", false_pos),
        ("missed", missed),
        ("precision", precision),
        ("precision_95_low", p_lo),
        ("precision_95_high", p_hi),
        ("recall", recall),
        ("recall_95_low", r_lo),
        ("recall_95_high", r_hi),
        ("correction_factor", factor),
        ("correction_factor_95_low", factor_lo),
        ("correction_factor_95_high", factor_hi),
        ("correction_factor_bootstrap_95_low", boot_lo),
        ("correction_factor_bootstrap_95_high", boot_hi),
        ("all_extracted_subevents", total_extracted),
        ("lulea_extracted_subevents", total_lulea),
        ("all_extra_after_dedup", extra_total),
        ("lulea_extra_after_dedup", extra_lulea),
        ("lulea_checked_rows", len(lchk)),
        ("lulea_manual_events", manual_lulea),
        ("lulea_parser_events", parser_lulea),
        ("lulea_manual_parser_factor", lulea_factor),
        ("lulea_factor_bootstrap_95_low", lulea_boot_lo),
        ("lulea_factor_bootstrap_95_high", lulea_boot_hi),
        ("lulea_extracted_estimated_true", lulea_extracted_est),
        ("lulea_extracted_estimated_95_low", lulea_extracted_low),
        ("lulea_extracted_estimated_95_high", lulea_extracted_high),
        ("lulea_extra_after_dedup_estimated_true", lulea_extra_est),
        ("lulea_extra_after_dedup_estimated_95_low", lulea_extra_low),
        ("lulea_extra_after_dedup_estimated_95_high", lulea_extra_high),
    ]
    pd.DataFrame(rows, columns=["metric", "value"]).to_csv(OUT, index=False, encoding="utf-8")

    md = [
        "# Validering av sammanfattningsparser",
        "",
        f"- Stickprov: **{len(s)}** sammanfattningar.",
        f"- Fullständigt manuellt kontrollerade rader: **{len(checked)}**.",
    ]
    if len(checked):
        md += [
            f"- Precision: **{fmt_pct(precision)}** (95 % Wilson {fmt_pct(p_lo)}–{fmt_pct(p_hi)}).",
            f"- Täckningsgrad/recall: **{fmt_pct(recall)}** (95 % Wilson {fmt_pct(r_lo)}–{fmt_pct(r_hi)}).",
            f"- Korrigeringsfaktor för extraherat antal: **{factor:.3f}** "
            f"(konservativt Wilson-baserat intervall {factor_lo:.3f}–{factor_hi:.3f}; "
            f"bootstrap på sammanfattningsnivå {boot_lo:.3f}–{boot_hi:.3f}).",
        ]
    else:
        md += [
            "- Precision och täckningsgrad beräknas när manuella QA-fält är ifyllda.",
            "- Rapporten publicerar inte ett påhittat felintervall innan kontrollen är gjord.",
        ]
    if len(lchk):
        md.append(
            f"- Luleå: manuellt räknade underhändelser/parserträffar i kontrollerade rader: "
            f"**{int(manual_lulea)}/{int(parser_lulea)}**, faktor **{lulea_factor:.3f}** "
            f"(bootstrap 95 % {lulea_boot_lo:.3f}–{lulea_boot_hi:.3f})."
        )
        if not pd.isna(extra_lulea):
            md.append(
                f"- Luleå, extra sammanfattningshändelser efter deduplicering: observerat **{int(extra_lulea)}**; "
                f"indikativt korrigerat **{lulea_extra_est:.0f}** "
                f"(bootstrap 95 % cirka **{lulea_extra_low:.0f}–{lulea_extra_high:.0f}**)."
            )
    md += [
        "",
        "## Tolkning",
        "",
        "Precision mäter hur stor andel av parserns träffar som är riktiga underhändelser. "
        "Täckningsgrad mäter hur stor andel av de manuellt identifierade underhändelserna som parsern hittar. "
        "Korrigeringsfaktorn är precision/täckningsgrad och ska endast användas som osäkerhetsanalys, inte för att "
        "ersätta den observerade serien i dashboarden utan tydlig märkning.",
        "",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(
        f"checked={len(checked)}/{len(s)} precision={precision if not pd.isna(precision) else 'NA'} "
        f"recall={recall if not pd.isna(recall) else 'NA'}"
    )


if __name__ == "__main__":
    main()
