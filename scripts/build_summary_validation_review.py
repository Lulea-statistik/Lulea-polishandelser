from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "summary_validation_sample.csv"
DETAILS = ROOT / "data" / "summary_details.csv"
OUT = ROOT / "data" / "summary_validation_review.tsv"

def clean(v: object, limit: int = 2200) -> str:
    s = "" if pd.isna(v) else str(v)
    return " ".join(s.replace("\r"," ").replace("\n"," ").replace("\t"," ").split())[:limit]

def main() -> None:
    sample = pd.read_csv(SAMPLE, dtype={"event_id":"string"}, low_memory=False)
    details = pd.read_csv(DETAILS, dtype={"parent_event_id":"string"}, low_memory=False)

    grouped = {}
    for eid, g in details.groupby("parent_event_id", dropna=False):
        bits = []
        for _, r in g.sort_values(["time","event_type_extracted"], na_position="last").iterrows():
            bits.append(
                f"{clean(r.get('time',''),20)}|{clean(r.get('municipality',''),30)}|"
                f"{clean(r.get('event_type_extracted',''),50)}|{clean(r.get('place_text',''),90)}"
            )
        grouped[str(eid)] = " || ".join(bits)

    review = sample[[
        "event_id","date","year","type_original","content",
        "extracted_count","parser_lulea_count",
        "manual_count","manual_lulea_count","parser_correct_count",
        "parser_false_positive_count","parser_missed_count","qa_note"
    ]].copy()
    review["content"] = review["content"].map(lambda x: clean(x, 2600))
    review["parser_items"] = review["event_id"].astype(str).map(grouped).fillna("")
    cols = [
        "event_id","date","year","type_original","content","parser_items",
        "extracted_count","parser_lulea_count","manual_count","manual_lulea_count",
        "parser_correct_count","parser_false_positive_count","parser_missed_count","qa_note"
    ]
    review[cols].to_csv(OUT, sep="\t", index=False, encoding="utf-8")
    print(f"review_rows={len(review)}")

if __name__ == "__main__":
    main()
