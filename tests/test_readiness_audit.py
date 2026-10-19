import csv
import json

import pandas as pd

from scripts import readiness_audit


def _uci_frame():
    rows = [
        # ID, LIMIT_BAL, SEX, EDUCATION, MARRIAGE, AGE, PAY_0..PAY_6, BILL1..6, PAY_AMT1..6, default
        [1, 1000, 1, 1, 1, 30, -1, -1, -1, -1, -1, -1, 100, 100, 100, 100, 100, 100, 0, 0, 0, 0, 0, 0, 0],
        [2, 1000, 2, 5, 0, 40, -2, 0, 0, 0, 0, 0, 2000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [3, 1000, 2, 2, 2, 50, 1, 2, 2, 2, 2, 2, -5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    return pd.DataFrame(rows, columns=readiness_audit.data_intake.UCI_COLUMNS)


def test_uci_audit_counts_rule_violations_on_untouched_data():
    result = readiness_audit.audit_uci_frame(_uci_frame())
    checks = result["candidate_check_violations_rows"]
    assert checks["EDUCATION_outside_documented"] == 1
    assert checks["MARRIAGE_outside_documented"] == 1
    assert checks["BILL_gt_LIMIT_rows"] == 1
    assert checks["BILL_gt_1_5x_LIMIT_rows"] == 1
    assert checks["BILL_AMT_negative_rows"] == 1
    # PAY codes -2 and 0 are undocumented: 6 of 18 cells.
    assert result["pay_cells_outside_documented_pct"] == round(100 * 6 / 18, 2)


def _sgcd_record(i, shock, field=None, null=False):
    view = {"purpose": "A43", "duration": 12}
    if null:
        view[field] = None
    return {
        "id": f"SGCD-{i:04d}", "label": 1,
        "metadata": {"stage": "test", "shock_semantic": shock, "shock_cosmetic": False, "shock_field": field},
        "value": {"json_view": view, "text_view": "Credit duration: roughly 12 months."},
    }


def test_sgcd_audit_separates_structured_nulls_from_text_shocks():
    records = [
        _sgcd_record(0, "F0"),
        _sgcd_record(1, "F1", "purpose", null=True),
        _sgcd_record(2, "F1", "purpose", null=False),
        _sgcd_record(3, "F4", "purpose"),
    ]
    result = readiness_audit.audit_sgcd_records(records)
    assert result["f1_records"] == 2
    assert result["f1_records_with_null_in_json_view"] == 1
    assert result["null_cells_outside_f1"] == 0
    assert result["records_by_stage_and_shock"]["test:F4"] == 1


def _write_table(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)


def test_secfintables_audit_compares_clean_twin_with_errloc(tmp_path):
    clean = [["", "2024"], ["Revenue", "10"], ["Cost", "(4)"], ["Net income", "6"]]
    corrupted = [["", "2024"], ["Revenue", "10"], ["Cost", "(4)%"], ["Net income", "6"]]
    loc = [{"row_name": "Cost", "col_idx": 1}, {"row_name": "Net income", "col_idx": 1}]
    for folder, name, rows, gt in (
        ("d1", "00001.csv", clean, {"errNum": 0, "errLoc": [], "errType": "", "missNum": 0}),
        ("d2", "00001_err_FMT_1.csv", corrupted, {"errNum": 2, "errLoc": loc, "errType": "FMT", "missNum": 0}),
    ):
        (tmp_path / folder).mkdir()
        _write_table(tmp_path / folder / name, rows)
        (tmp_path / folder / f"groundtruth_{folder}.json").write_text(json.dumps([{"fileName": name, **gt}]))
    result = readiness_audit.audit_secfintables_dir(tmp_path, ["d1", "d2"])
    assert result["clean_twin_pairs"] == 1
    assert result["clean_twin_changed_cells"] == 1
    assert result["clean_twin_changed_cells_inside_errLoc"] == 1
    assert result["clean_twin_errLoc_cells"] == 2
    assert result["clean_twin_changed_cells_originally_parenthesised"] == 1
