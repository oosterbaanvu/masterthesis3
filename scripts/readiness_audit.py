#!/usr/bin/env python3
"""Dataset readiness audit: reproduce the figures in docs/research/dataset_readiness_report.md.

Read-only. Each audit inspects the verified local copy (run data_intake.py
first) and writes results/readiness/<dataset>.json (untracked). Nothing here
trains a detector, injects errors, or treats outcome labels (default, fraud,
credit risk) as data-quality labels.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sys
from pathlib import Path

try:
    from scripts import data_intake
except ImportError:  # executed as a script
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts import data_intake

ROOT = data_intake.ROOT
OUT_DIR = ROOT / "results/readiness"

# Codes documented on the UCI page; the observed data also uses others.
UCI_DOCUMENTED = {
    "SEX": {1, 2},
    "EDUCATION": {1, 2, 3, 4},
    "MARRIAGE": {1, 2, 3},
    "PAY": {-1, 1, 2, 3, 4, 5, 6, 7, 8, 9},
}
UCI_PAY = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
UCI_BILL = [f"BILL_AMT{i}" for i in range(1, 7)]
UCI_PAYAMT = [f"PAY_AMT{i}" for i in range(1, 7)]

# Sentinel (missing) encodings documented in the BAF datasheet (Q7).
BAF_NEGATIVE_MEANS_MISSING = [
    "prev_address_months_count", "current_address_months_count", "intended_balcon_amount",
    "bank_months_count", "session_length_in_minutes", "device_distinct_emails_8w",
]


def pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 2) if d else 0.0


# --- UCI ---------------------------------------------------------------------

def audit_uci_frame(f) -> dict:
    """Failure rates of candidate conventional checks on the untouched table."""
    n = len(f)
    pay_cells = f[UCI_PAY].stack()
    bill = f[UCI_BILL].to_numpy()
    limit = f[["LIMIT_BAL"]].to_numpy()
    checks = {
        "not_null_any_column": int(f.isna().any(axis=1).sum()),
        "unique_ID_violations": int(n - f["ID"].nunique()),
        "SEX_outside_documented": int((~f["SEX"].isin(UCI_DOCUMENTED["SEX"])).sum()),
        "EDUCATION_outside_documented": int((~f["EDUCATION"].isin(UCI_DOCUMENTED["EDUCATION"])).sum()),
        "MARRIAGE_outside_documented": int((~f["MARRIAGE"].isin(UCI_DOCUMENTED["MARRIAGE"])).sum()),
        "AGE_outside_18_100": int((~f["AGE"].between(18, 100)).sum()),
        "LIMIT_BAL_non_positive": int((f["LIMIT_BAL"] <= 0).sum()),
        "PAY_AMT_negative_rows": int((f[UCI_PAYAMT] < 0).any(axis=1).sum()),
        "BILL_AMT_negative_rows": int((f[UCI_BILL] < 0).any(axis=1).sum()),
        "BILL_gt_LIMIT_rows": int((bill > limit).any(axis=1).sum()),
        "BILL_gt_1_5x_LIMIT_rows": int((bill > 1.5 * limit).any(axis=1).sum()),
    }
    return {
        "rows": n,
        "columns": len(f.columns),
        "null_cells": int(f.isna().sum().sum()),
        "duplicate_rows_excluding_ID": int(f.drop(columns="ID").duplicated().sum()),
        "pay_cells_outside_documented_pct": pct(int((~pay_cells.isin(UCI_DOCUMENTED["PAY"])).sum()), len(pay_cells)),
        "pay_value_counts": {c: {int(k): int(v) for k, v in f[c].value_counts().sort_index().items()} for c in UCI_PAY},
        "education_value_counts": {int(k): int(v) for k, v in f["EDUCATION"].value_counts().sort_index().items()},
        "marriage_value_counts": {int(k): int(v) for k, v in f["MARRIAGE"].value_counts().sort_index().items()},
        "candidate_check_violations_rows": checks,
        "candidate_check_violations_pct": {k: pct(v, n) for k, v in checks.items()},
        "outcome_label_column": "default payment next month (credit outcome, not a data-quality label)",
    }


def audit_uci() -> dict:
    import pandas as pd
    data_intake.check_uci()
    f = pd.read_excel(data_intake.UCI_XLS, header=1, engine="xlrd")
    f.columns = [str(c).strip() for c in f.columns]
    return audit_uci_frame(f)


# --- BAF ---------------------------------------------------------------------

def audit_baf() -> dict:
    import pandas as pd
    if not data_intake.BAF_CSV.is_file():
        return {"status": "BLOCKED", "reason": f"{data_intake.rel(data_intake.BAF_CSV)} not present; manual Kaggle download and licence clearance pending"}
    data_intake.check_baf()
    f = pd.read_csv(data_intake.BAF_CSV, low_memory=False)
    cols = [c for c in BAF_NEGATIVE_MEANS_MISSING if c in f.columns]
    return {
        "status": "audited",
        "rows": len(f),
        "columns": list(f.columns),
        "rows_per_month": {int(k): int(v) for k, v in f["month"].value_counts().sort_index().items()},
        "null_cells": int(f.isna().sum().sum()),
        "negative_sentinel_pct": {c: pct(int((f[c] < 0).sum()), len(f)) for c in cols},
        "duplicate_rows": int(f.duplicated().sum()),
        "outcome_label_column": "fraud_bool (fraud outcome, not a data-quality label)",
    }


# --- SGCD ----------------------------------------------------------------------

def audit_sgcd_records(records: list[dict]) -> dict:
    by_stage_shock = collections.Counter(f"{r['metadata']['stage']}:{r['metadata']['shock_semantic']}" for r in records)
    f1 = [r for r in records if r["metadata"]["shock_semantic"] == "F1"]
    f1_null = sum(1 for r in f1 if r["value"]["json_view"].get(r["metadata"]["shock_field"]) is None)
    nulls_outside_f1 = sum(
        1 for r in records if r["metadata"]["shock_semantic"] != "F1"
        for v in r["value"]["json_view"].values() if v is None
    )
    approx = sum(1 for r in records if re.search(r"\b(roughly|around|about|approximately)\b", r["value"]["text_view"]))
    return {
        "records": len(records),
        "attributes_in_json_view": sorted({len(r["value"]["json_view"]) for r in records}),
        "records_by_stage_and_shock": dict(sorted(by_stage_shock.items())),
        "cosmetic_records": sum(1 for r in records if r["metadata"]["shock_cosmetic"]),
        "f1_records": len(f1),
        "f1_records_with_null_in_json_view": f1_null,
        "null_cells_outside_f1": nulls_outside_f1,
        "records_with_vague_numeric_wording_in_text": approx,
        "note": "Per the publisher README, only F1 touches the structured view (as null); F2/F3/F4 and numeric "
                "noise alter text_view only. Checking json_view against the UCI mother dataset needs german.data.",
    }


def audit_sgcd() -> dict:
    data_intake.check_sgcd()
    path = data_intake.SGCD_DIR / "data/SGCDataset.jsonl"
    return audit_sgcd_records([json.loads(line) for line in path.open(encoding="utf-8")])


# --- SEC-FinTables ------------------------------------------------------------

def _load_csv(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


def audit_secfintables_dir(base: Path, data_dirs: list[str]) -> dict:
    tables = {d: {p.name[:5]: p for p in (base / d).glob("*.csv")} for d in data_dirs}
    truth = {}
    for d in data_dirs:
        gt_file = next((base / d).glob("groundtruth_*.json"))
        truth[d] = {g["fileName"][:5]: g for g in json.loads(gt_file.read_text(encoding="utf-8"))}
    per_dir = {}
    for d in data_dirs:
        gts = truth[d].values()
        types = collections.Counter(g["errType"] if isinstance(g["errType"], str) else "_".join(g["errType"]) for g in gts)
        per_dir[d] = {
            "tables": len(tables[d]),
            "tables_flagged_with_errors": sum(1 for g in gts if g["errNum"] > 0),
            "annotated_errLoc_cells": sum(len(g["errLoc"]) for g in gts),
            "error_type_counts": dict(types.most_common()),
            "errNum_equals_len_errLoc": all(g["errNum"] == len(g["errLoc"]) for g in gts),
            "err_filename_but_errNum_0": sum(1 for g in gts if "_err_" in g["fileName"] and g["errNum"] == 0),
            "clean_filename_but_errNum_gt_0": sum(1 for g in gts if "_err_" not in g["fileName"] and g["errNum"] > 0),
        }
    # Tables published uncorrupted in one folder and corrupted in another give
    # the only directly observable injected edits.
    ids = set.intersection(*(set(t) for t in tables.values()))
    pairs = changed = changed_in_loc = loc_cells = zero_change = paren = shape_diff = 0
    same_target = diff_target = 0
    for i in sorted(ids):
        clean_dirs = [d for d in data_dirs if "_err_" not in tables[d][i].name]
        err_dirs = [d for d in data_dirs if "_err_" in tables[d][i].name]
        if not clean_dirs or not err_dirs:
            continue
        a = _load_csv(tables[clean_dirs[0]][i])
        targets = []
        for d in err_dirs:
            b = _load_csv(tables[d][i])
            pairs += 1
            if len(a) != len(b) or any(len(x) != len(y) for x, y in zip(a, b)):
                shape_diff += 1
                continue
            cells = [(r, c) for r in range(len(a)) for c in range(len(a[r])) if a[r][c] != b[r][c]]
            locs = {(loc["row_name"], loc["col_idx"]) for loc in truth[d][i]["errLoc"]}
            changed += len(cells)
            loc_cells += len(locs)
            changed_in_loc += sum((a[r][0], c) in locs for r, c in cells)
            zero_change += not cells
            paren += sum("(" in a[r][c] for r, c in cells)
            targets.append(frozenset(cells))
        if len(targets) >= 2:
            same_target += len(set(targets)) == 1
            diff_target += len(set(targets)) != 1
    clean_artefacts = collections.Counter()
    first = data_dirs[0]
    clean_tables = [p for p in tables[first].values() if "_err_" not in p.name]
    rows, cols = [], []
    for p in tables[first].values():
        t = _load_csv(p)
        rows.append(len(t))
        cols.append(max(len(r) for r in t))
    for p in clean_tables:
        t = _load_csv(p)
        if any(x.count("(") != x.count(")") for r in t for x in r[1:]):
            clean_artefacts["unbalanced_parentheses"] += 1
        if any(len(x) > 200 for r in t for x in r):
            clean_artefacts["cell_over_200_chars"] += 1
        if len({r[0] for r in t}) != len(t):
            clean_artefacts["duplicate_row_labels"] += 1
    rows.sort()
    cols.sort()
    return {
        "per_folder": per_dir,
        "table_ids_shared_by_all_folders": len(ids),
        "table_shape_rows_median_max": [rows[len(rows) // 2], rows[-1]],
        "table_shape_cols_median_max": [cols[len(cols) // 2], cols[-1]],
        "clean_twin_pairs": pairs,
        "clean_twin_pairs_shape_mismatch": shape_diff,
        "clean_twin_changed_cells": changed,
        "clean_twin_changed_cells_inside_errLoc": changed_in_loc,
        "clean_twin_errLoc_cells": loc_cells,
        "clean_twin_err_files_identical_to_clean": zero_change,
        "clean_twin_changed_cells_originally_parenthesised": paren,
        "tables_with_same_injected_cells_across_folders": same_target,
        "tables_with_different_injected_cells_across_folders": diff_target,
        "clean_tables_in_first_folder": len(clean_tables),
        "clean_tables_with_extraction_artefacts": dict(clean_artefacts),
    }


def audit_secfintables() -> dict:
    data_intake.check_secfintables()
    exp = data_intake.expected("sec_fintables")
    return audit_secfintables_dir(data_intake.SECFT_DIR, exp["data_dirs"])


AUDITS = {"uci": audit_uci, "baf": audit_baf, "sgcd": audit_sgcd, "secfintables": audit_secfintables}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("datasets", nargs="*", help=f"subset of {sorted(AUDITS)} (default: all)")
    args = parser.parse_args()
    unknown = set(args.datasets) - set(AUDITS)
    if unknown:
        parser.error(f"unknown dataset(s): {sorted(unknown)}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failures = 0
    for name in args.datasets or AUDITS:
        try:
            result = AUDITS[name]()
        except Exception as exc:
            failures += 1
            print(f"[NOT AUDITED] {name}: {exc}")
            continue
        target = OUT_DIR / f"{name}.json"
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[AUDITED] {name} -> {data_intake.rel(target)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
