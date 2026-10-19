# Financial Data Quality — MSc thesis

**Scope:** Financial-source onboarding, baseline checks, controlled error stress tests, and the incremental value of learned cell-level anomaly/error detectors. The environment uses **public research data only**, not Rabobank internal datasets.

**Current phase:** Dataset readiness. The strong dbt baseline and ML-detector experiments have **not started**. Previous feasibility reports are retained for context, not passed off as new experiments. See [`docs/research/dataset_readiness_report.md`](docs/research/dataset_readiness_report.md).

## Datasets

| Dataset | Role | Status | Git policy | Cell-error ground truth? |
|---|---|---|---|---|
| UCI Default of Credit Card Clients | Controlled experiments (primary) | Ready | Original XLS tracked (CC BY 4.0) | No |
| Feedzai BAF Base | Controlled experiments (secondary); months 6–7 as untouched later batch | **Blocked**: manual Kaggle download + licence clearance | Never committed | No (`fraud_bool` is **not** a cell-error label) |
| Santander AI SGCD v0.1 | Assessed external candidate | Not suitable (shocks are in the text view) | Fetched at pinned commit, ignored | Partial |
| SEC-FinTables | Assessed external candidate | Not suitable (relation-level labels, no corrected values, no licence) | Fetched at pinned commit, ignored | Partial |
| Raha Flights | Optional non-financial genuine-error check | Not acquired in this repo | – | Yes (non-financial) |

TableEG Credit/Marketing and AuditBench remain excluded (see `docs/research/decision_log.md`). Expected sources, commits, hashes and licences: [`data/manifests/datasets.json`](data/manifests/datasets.json).

## Set up and verify data

Requires Python 3.10+.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-data.txt

python scripts/data_intake.py verify-uci           # tracked XLS
# without the tracked file: download-uci, or import-uci <official UCI zip>
python scripts/data_intake.py fetch-sgcd
python scripts/data_intake.py fetch-secfintables
python scripts/data_intake.py verify-external
python scripts/data_intake.py status               # all four datasets
python scripts/readiness_audit.py                  # readiness figures -> results/readiness/
python -m pytest -q
```

For BAF, download **only `Base.csv`** from the official Kaggle page (details in `data/README.md`), place it at `data/raw/baf/Base.csv`, then run `python scripts/data_intake.py verify-baf`. `verify-all` fails until both core datasets (UCI and BAF) exist and validate.

Verification is limited to provenance, hashes and known structure. It **does not** certify that contents are error-free or that usage rights are settled.

## Repository layout

```
data/raw/uci/        original UCI XLS (tracked) + attribution
data/raw/baf/        local-only BAF Base.csv (ignored)
data/external/       pinned external benchmarks (ignored)
data/processed/      future derived/corrupted data (ignored)
data/manifests/      datasets.json (tracked); *.local.json verification results (ignored)
scripts/             data_intake.py (acquire/verify), readiness_audit.py (read-only audits)
tests/               code tests on synthetic fixtures; CI runs without datasets
docs/                proposal, pilot summaries, decision log, readiness report
```

Never commit BAF data, SEC-FinTables tables, corrupted copies or results. CI runs code tests only and cannot certify local-only datasets.

## Next milestone

After the readiness report is reviewed and BAF is cleared: design a justified strong conventional baseline (dbt, custom SQL/business checks, numerical/statistical controls), measure its failure rates on the untouched data, and only then compare the incremental yield of learned detectors under prespecified, held-out injection scenarios.

## Research materials

- `docs/proposal/`: most recent revised research proposal
- `docs/research/pilot_summaries/`: four earlier pilot summaries (Dutch); not a replacement for raw code/results
- `docs/research/decision_log.md`: dataset and scope decisions
- `docs/research/dataset_readiness_report.md`: readiness and benchmark study (this phase)

Keep the repository private, disclose the limits of public datasets, and never suggest the tool has been deployed inside a bank.
