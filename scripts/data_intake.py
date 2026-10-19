#!/usr/bin/env python3
"""Acquire, verify and register the thesis datasets.

Core datasets: UCI Default of Credit Card Clients and Feedzai BAF Base.
External benchmark candidates: Santander SGCD and SEC-FinTables, fetched at a
pinned upstream commit.

No detector training, corruption, or data cleaning is performed here. Original
source bytes remain unchanged. Expected pins and hashes live in
data/manifests/datasets.json; see data/README.md for source and license notes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "data/manifests"
EXPECTED_MANIFEST = MANIFEST_DIR / "datasets.json"
UCI_XLS = ROOT / "data/raw/uci/default_of_credit_card_clients.xls"
BAF_CSV = ROOT / "data/raw/baf/Base.csv"
SGCD_DIR = ROOT / "data/external/sgcd"
SECFT_DIR = ROOT / "data/external/sec_fintables"
UCI_URL = "https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip"
UCI_ARCHIVE_MEMBER = "default of credit card clients.xls"
SGCD_RAW_URL = "https://raw.githubusercontent.com/SantanderAI/sota-stressed-datasets/{commit}/{subdir}/{path}"
UCI_COLUMNS = [
    "ID", "LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE",
    "PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6",
    "BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6",
    "PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6",
    "default payment next month",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for piece in iter(lambda: f.read(1024 * 1024), b""):
            h.update(piece)
    return h.hexdigest()


def tree_sha256(base: Path, subdirs: list[str]) -> str:
    """Hash of sorted '<sha256>  <relative path>' lines for all files in subdirs."""
    paths = sorted(p.relative_to(base).as_posix() for sub in subdirs for p in (base / sub).rglob("*") if p.is_file())
    lines = "".join(f"{sha256(base / p)}  {p}\n" for p in paths)
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def expected(key: str) -> dict:
    return json.loads(EXPECTED_MANIFEST.read_text(encoding="utf-8"))["datasets"][key]


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


# --- UCI ---------------------------------------------------------------------

def extract_uci_from_archive(archive: Path) -> None:
    """Copy the original XLS out of an official UCI archive without changing it."""
    with zipfile.ZipFile(archive) as z:
        matches = [i for i in z.infolist() if Path(i.filename).name.lower() == UCI_ARCHIVE_MEMBER]
        if len(matches) != 1:
            raise ValueError(f"Expected one XLS inside UCI zip; found {len(matches)}")
        UCI_XLS.parent.mkdir(parents=True, exist_ok=True)
        try:
            with z.open(matches[0]) as source, UCI_XLS.open("wb") as dest:
                shutil.copyfileobj(source, dest)
        except Exception:
            UCI_XLS.unlink(missing_ok=True)
            raise
    print(f"[OK] Extracted {rel(UCI_XLS)}, sha256={sha256(UCI_XLS)}")


def download_uci() -> None:
    """Download the official UCI archive and store the original XLS unchanged."""
    if UCI_XLS.exists():
        print(f"[EXISTS] {rel(UCI_XLS)} (will not overwrite)")
        return
    print(f"Downloading original UCI archive from: {UCI_URL}")
    req = urllib.request.Request(UCI_URL, headers={"User-Agent": "FinancialDataQualityThesis/0.1"})
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "uci.zip"
        with urllib.request.urlopen(req, timeout=60) as response, archive.open("wb") as out:
            shutil.copyfileobj(response, out)
        print(f"       archive sha256: {sha256(archive)}")
        extract_uci_from_archive(archive)


def import_uci(archive: Path) -> None:
    """Offline alternative to download-uci: use an archive the researcher downloaded from UCI."""
    if UCI_XLS.exists():
        print(f"[EXISTS] {rel(UCI_XLS)} (will not overwrite)")
        return
    print(f"Importing UCI archive {archive} (sha256 {sha256(archive)})")
    extract_uci_from_archive(archive)


def check_uci() -> dict:
    import pandas as pd
    exp = expected("uci_credit")
    if not UCI_XLS.is_file():
        raise FileNotFoundError(f"Missing {rel(UCI_XLS)}. Run: python scripts/data_intake.py download-uci")
    digest = sha256(UCI_XLS)
    if exp["sha256"] and digest != exp["sha256"]:
        raise ValueError(f"UCI XLS sha256 {digest} differs from pinned {exp['sha256']}; source bytes changed or another version")
    # Official XLS has a first row with X1..Y variable identifiers and a
    # second row with the human-readable column names.
    frame = pd.read_excel(UCI_XLS, header=1, engine="xlrd")
    frame.columns = [str(c).strip() for c in frame.columns]
    observed = list(frame.columns)
    if observed != UCI_COLUMNS:
        raise ValueError(f"Unexpected UCI schema: {observed}. Expected {UCI_COLUMNS}.")
    if len(frame) != exp["rows"]:
        raise ValueError(f"Expected {exp['rows']:,} UCI rows, got {len(frame):,}")
    if frame["ID"].isna().any() or frame["ID"].nunique() != len(frame):
        raise ValueError("ID column must have 30,000 non-null unique IDs")
    return {
        "dataset": exp["name"], "key": "uci_credit", "status": "verified-file-hash-and-schema",
        "source": exp["source"], "doi": exp["doi"], "license": exp["license"],
        "relative_path": rel(UCI_XLS), "rows": len(frame), "columns": len(frame.columns),
        "sha256": digest, "contains_ground_truth_for_cell_errors": False,
        "warning": "Public dataset is not independently verified as cell-level error-free; "
                   "'default payment next month' is a credit outcome, not a data-quality label.",
    }


# --- BAF ---------------------------------------------------------------------

def check_baf() -> dict:
    import pandas as pd
    exp = expected("baf_base")
    if not BAF_CSV.is_file():
        raise FileNotFoundError(f"Missing {rel(BAF_CSV)}. Download Base.csv from the official Kaggle dataset.")
    digest = sha256(BAF_CSV)
    if exp["sha256"] and digest != exp["sha256"]:
        raise ValueError(f"BAF Base.csv sha256 {digest} differs from pinned {exp['sha256']}")
    total = 0
    columns = None
    months = set()
    for chunk in pd.read_csv(BAF_CSV, chunksize=50000, low_memory=False):
        if columns is None:
            columns = list(chunk.columns)
            if "month" not in columns or "fraud_bool" not in columns:
                raise ValueError(f"Missing required BAF columns month and/or fraud_bool. Observed: {columns}")
        total += len(chunk)
        month_numeric = pd.to_numeric(chunk["month"], errors="coerce")
        if month_numeric.isna().any():
            raise ValueError("BAF 'month' must contain numeric, non-null values")
        if not (month_numeric == month_numeric.astype(int)).all():
            raise ValueError("BAF 'month' must contain whole-month indexes")
        months.update(int(v) for v in month_numeric.unique().tolist())
    if total != exp["rows"]:
        raise ValueError(f"Expected {exp['rows']:,} BAF Base records, got {total:,}")
    # The CSV may include a separate saved index column, depending on export.
    if not set(exp["months"]).issubset(months):
        raise ValueError(f"Expected monthly batch indicators 0..7; got {sorted(months)}")
    return {
        "dataset": exp["name"], "key": "baf_base", "status": "verified-file-and-basic-schema",
        "source": exp["source"], "upstream": exp["upstream"], "license": exp["license"],
        "relative_path": rel(BAF_CSV), "rows": total, "columns": len(columns or []),
        "months_observed": sorted(months), "sha256": digest,
        "sha256_pinned": bool(exp["sha256"]),
        "contains_ground_truth_for_cell_errors": False,
        "warning": "fraud_bool is NOT a data-quality/error label; no redistribution of raw or modified BAF files without permission.",
    }


# --- External benchmarks -----------------------------------------------------

def fetch_sgcd() -> None:
    exp = expected("sgcd")
    for path in exp["files"]:
        target = SGCD_DIR / path
        if target.is_file() and sha256(target) == exp["files"][path]:
            print(f"[EXISTS] {rel(target)}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        url = SGCD_RAW_URL.format(commit=exp["commit"], subdir=exp["subdir"], path=path)
        req = urllib.request.Request(url, headers={"User-Agent": "FinancialDataQualityThesis/0.1"})
        with urllib.request.urlopen(req, timeout=60) as response, target.open("wb") as out:
            shutil.copyfileobj(response, out)
        print(f"[OK] {rel(target)}")
    (SGCD_DIR / "UPSTREAM_COMMIT").write_text(exp["commit"] + "\n", encoding="utf-8")


def check_sgcd() -> dict:
    exp = expected("sgcd")
    for path, digest in exp["files"].items():
        target = SGCD_DIR / path
        if not target.is_file():
            raise FileNotFoundError(f"Missing {rel(target)}. Run: python scripts/data_intake.py fetch-sgcd")
        if sha256(target) != digest:
            raise ValueError(f"{rel(target)} sha256 differs from pinned commit {exp['commit']}")
    records = [json.loads(line) for line in (SGCD_DIR / "data/SGCDataset.jsonl").open(encoding="utf-8")]
    if len(records) != exp["rows"]:
        raise ValueError(f"Expected {exp['rows']} SGCD records, got {len(records)}")
    return {
        "dataset": exp["name"], "key": "sgcd", "status": "verified-pinned-file-hashes",
        "source": exp["source"], "commit": exp["commit"], "license": exp["license"],
        "relative_path": rel(SGCD_DIR), "rows": len(records),
        "columns": len(records[0]["value"]["json_view"]), "sha256": exp["files"]["data/SGCDataset.jsonl"],
        "contains_ground_truth_for_cell_errors": "partial (shock metadata; see readiness report)",
        "warning": "The credit-risk 'label' is not a data-quality label.",
    }


def fetch_secfintables() -> None:
    exp = expected("sec_fintables")
    if (SECFT_DIR / ".git").is_dir():
        head = subprocess.run(["git", "-C", str(SECFT_DIR), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
        if head == exp["commit"]:
            print(f"[EXISTS] {rel(SECFT_DIR)} at {head}")
            return
        raise RuntimeError(f"{rel(SECFT_DIR)} is at {head}, expected {exp['commit']}; remove it and fetch again")
    SECFT_DIR.mkdir(parents=True, exist_ok=True)
    env_git = ["git", "-C", str(SECFT_DIR)]
    subprocess.run(env_git + ["init", "-q"], check=True)
    subprocess.run(env_git + ["remote", "add", "origin", exp["source"]], check=True)
    subprocess.run(env_git + ["fetch", "-q", "--depth", "1", "origin", exp["commit"]], check=True)
    subprocess.run(env_git + ["checkout", "-q", "--detach", "FETCH_HEAD"], check=True)
    print(f"[OK] {rel(SECFT_DIR)} at {exp['commit']}")


def check_secfintables() -> dict:
    exp = expected("sec_fintables")
    if not SECFT_DIR.is_dir():
        raise FileNotFoundError(f"Missing {rel(SECFT_DIR)}. Run: python scripts/data_intake.py fetch-secfintables")
    for sub in exp["data_dirs"]:
        csvs = list((SECFT_DIR / sub).glob("*.csv"))
        if len(csvs) != exp["csv_per_dir"]:
            raise ValueError(f"{sub}: expected {exp['csv_per_dir']} CSV tables, got {len(csvs)}")
    digest = tree_sha256(SECFT_DIR, exp["data_dirs"])
    if digest != exp["data_tree_sha256"]:
        raise ValueError(f"SEC-FinTables data tree sha256 {digest} differs from pinned {exp['data_tree_sha256']}")
    return {
        "dataset": exp["name"], "key": "sec_fintables", "status": "verified-pinned-data-tree",
        "source": exp["source"], "commit": exp["commit"], "license": exp["license"],
        "relative_path": rel(SECFT_DIR), "rows": exp["csv_per_dir"] * len(exp["data_dirs"]),
        "columns": None, "sha256": digest,
        "contains_ground_truth_for_cell_errors": "partial (error type and errLoc; no corrected values)",
        "warning": "No licence declared upstream: keep local, do not redistribute tables or derivatives.",
    }


# --- Manifests and CLI ---------------------------------------------------------

CHECKS = {
    "uci": ("uci_credit", check_uci),
    "baf": ("baf_base", check_baf),
    "sgcd": ("sgcd", check_sgcd),
    "secfintables": ("sec_fintables", check_secfintables),
}
CORE = ("uci", "baf")
EXTERNAL = ("sgcd", "secfintables")


def write_manifest(info: dict) -> None:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    info["verified_at_utc"] = datetime.now(timezone.utc).isoformat()
    target = MANIFEST_DIR / f"{info['key']}.local.json"
    target.write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    rows = f"{info['rows']:,} records" if info.get("rows") is not None else ""
    print(f"[PASS] {info['dataset']}: {rows}")
    print(f"       sha256: {info['sha256']}")
    print(f"       private local manifest: {rel(target)}")


def run_checks(names: tuple[str, ...]) -> int:
    failures = 0
    for name in names:
        try:
            write_manifest(CHECKS[name][1]())
        except Exception as exc:
            failures += 1
            print(f"[NOT READY] {name}: {exc}")
    print(f"Status: {len(names) - failures}/{len(names)} dataset(s) locally verified.")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=[
        "download-uci", "import-uci", "fetch-sgcd", "fetch-secfintables",
        "verify-uci", "verify-baf", "verify-sgcd", "verify-secfintables",
        "status", "verify-all", "verify-external",
    ])
    parser.add_argument("archive", nargs="?", type=Path, help="UCI zip archive for import-uci")
    args = parser.parse_args()
    if args.command == "download-uci":
        download_uci()
        return 0
    if args.command == "import-uci":
        if args.archive is None:
            parser.error("import-uci needs the path of the UCI zip archive")
        import_uci(args.archive)
        return 0
    if args.command == "fetch-sgcd":
        fetch_sgcd()
        return 0
    if args.command == "fetch-secfintables":
        fetch_secfintables()
        return 0
    if args.command.startswith("verify-") and args.command[7:] in CHECKS:
        return 1 if run_checks((args.command[7:],)) else 0
    if args.command == "verify-external":
        return 1 if run_checks(EXTERNAL) else 0
    failures = run_checks(CORE)
    if args.command == "verify-all" and failures:
        print(f"[FAIL] {failures} required core dataset(s) unavailable/invalid.")
        return 1
    if args.command == "status":
        run_checks(EXTERNAL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
