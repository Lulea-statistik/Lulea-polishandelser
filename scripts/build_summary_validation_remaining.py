from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "data" / "summary_validation_sample.csv"
out = ROOT / "data" / "summary_validation_remaining.tsv"

df = pd.read_csv(src, dtype={"event_id":"string"}, low_memory=False)
remaining = df[df["parser_correct_count"].isna()].copy()
cols = [
    "event_id","date","year","type_original","content",
    "extracted_count","parser_lulea_count"
]
remaining[cols].to_csv(out, sep="\t", index=False, encoding="utf-8")
print(f"remaining_rows={len(remaining)}")
