# Data-first handoff for the next coding session

> **Status 19 October 2026:** steps 1–3 and 7 done for UCI; BAF (steps 4–5) BLOCKED on manual download and licence clearance. External candidates SGCD and SEC-FinTables assessed and not selected. See `docs/research/dataset_readiness_report.md`.

## Aim

Continue in this fresh repository. Do not start detector work or dbt rule engineering until the two primary input sources are verified or explicitly marked blocked. This repo is a clean restart; pilot summaries are reference documents, not newly run results.

## Required actions, in order

1. Confirm source and version of UCI Credit and Feedzai BAF Base. Do not conflate UCI Default Credit Card Clients with Kaggle Give Me Some Credit / TableEG Credit.
2. Use `python scripts/data_intake.py download-uci` to obtain the official UCI XLS, followed by `verify-uci`. Do not alter the source file.
3. Confirm the UCI schema and row count (30,000) and capture SHA-256. Because the UCI source is licensed CC BY 4.0, the verified original XLS can be committed with attribution.
4. Ask the researcher to place BAF `Base.csv` from the official Kaggle source under `data/raw/baf/`. Never generate/fabricate this dataset or silently substitute a mirrored copy. Do not commit BAF bytes; preserve the noncommercial/no-derivatives uncertainty for supervisor review.
5. Run `verify-baf`, which checks one million rows and months 0–7, and store local SHA-256. Verify the exact upstream license, particularly the publisher datasheet and current Kaggle notice. A GitHub source-code license is not necessarily the dataset license.
6. Run `python scripts/data_intake.py verify-all` and `python -m pytest -q`.
7. Produce a simple readiness report: actual on-disk paths, sizes, counts, hashes, licensing caveats, original provenance, Git tracked/untracked state, and blockers.
8. Do not claim the research data is error-free, do not treat fraud/default labels as data-quality labels, and do not launch the next dbt/CDC experiment until readiness is reviewed.

## Acceptance criteria

- A fresh clone can fetch and verify UCI automatically.
- BAF is available in the authorized local environment, or explicitly BLOCKED awaiting user download/license clearance.
- `verify-all` passes only if both required raw sources exist and validate.
- Repository contains no restricted raw data or accidentally generated corrupted test copies.
- Research reports remain accessible but no legacy experiment code silently overwrites new assumptions.
