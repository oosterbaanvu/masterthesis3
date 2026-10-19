# Financial dataset acquisition and provenance

## UCI — Default of Credit Card Clients (primary)

- Official source: https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients
- Permanent DOI: https://doi.org/10.24432/C55S3H
- Official archive: https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip
- License (as stated on UCI): Creative Commons Attribution 4.0 International (CC BY 4.0).
- Credit: I-Cheng Yeh. *Default of Credit Card Clients*, UCI Machine Learning Repository (2009), DOI 10.24432/C55S3H.
- File: `data/raw/uci/default_of_credit_card_clients.xls` (original XLS, unchanged, tracked; sha256 pinned in `manifests/datasets.json`).
- Offline alternative to `download-uci`: `python scripts/data_intake.py import-uci <official UCI zip>`.
- Expected records: 30,000; schema: ID, 23 features, 1 outcome column (25 columns total).
- `default payment next month` is a target for default prediction, **not an error/dirty-cell label**.
- The file may include out-of-documentation codes; validation checks should not automatically call every such cell corrupted.

Run `python scripts/data_intake.py download-uci`, then `verify-uci` to document hash/shape. The original file is eligible for sharing under CC BY 4.0 with credit and license notice. Any adapted file must disclose changes.

## Feedzai Bank Account Fraud — Base (secondary)

- Official research repository: https://github.com/feedzai/bank-account-fraud
- Official Kaggle dataset link: https://www.kaggle.com/datasets/sgpjesus/bank-account-fraud-dataset-neurips-2022
- Intended file: `data/raw/baf/Base.csv` (unmodified Base variant).
- Expected records: 1,000,000; required fields `month` and `fraud_bool`; expected months 0–7.
- The research publisher's datasheet states **CC BY-NC-ND 4.0**. Other distribution pages may state different license terms. Confirm the exact applicable terms and whether the proposed industry-linked thesis use is permitted **before** sharing derivatives or committing data.
- **Never** treat `fraud_bool` as ground truth for malformed/incorrect data cells.
- Dataset is synthetic, not actual account applications from the bank where this thesis is hosted.

Download Base.csv via the official page after logging in, then place it in `data/raw/baf/Base.csv`. It is intentionally ignored by Git. Use `python scripts/data_intake.py verify-baf` to validate and produce a private local manifest. Do not commit the raw file, modified versions, or the private manifest.

## Dataset readiness policy

1. File exists and is from the stated source.
2. Hash (SHA-256) and date recorded by verification.
3. Expected rows, columns, and key fields verified.
4. Intended use and licensing checked.
5. Raw bytes protected from changes; any synthetic errors stored separately.
6. Fixed train/selection/test splits and calibration/ground-truth assumptions will be planned in the experimental phase, **not** during acquisition.

## External benchmark candidates (assessed, not selected)

- **Santander AI SGCD v0.1** — https://github.com/SantanderAI/sota-stressed-datasets, pinned commit in `manifests/datasets.json`, CC BY 4.0. Fetch with `fetch-sgcd` into `data/external/sgcd/` (ignored).
- **SEC-FinTables** — https://github.com/XIEFOX/SEC-Fintables, pinned commit, **no licence declared**. Fetch with `fetch-secfintables` into `data/external/sec_fintables/` (ignored). Do not redistribute.

Both were assessed in `docs/research/dataset_readiness_report.md` and are not part of the confirmatory selection.

## Current acquisition state (19 October 2026)

- UCI: original XLS tracked at `data/raw/uci/default_of_credit_card_clients.xls` (from the researcher-supplied official archive; UCI site blocked in the build environment).
- BAF: **not present** — manual Kaggle download required.
- SGCD and SEC-FinTables: fetched and hash-verified locally at the pinned commits.
