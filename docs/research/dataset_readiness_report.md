# Dataset readiness and benchmark study

| | |
|---|---|
| Date | 19 October 2026 |
| Status | Concept for supervisor review. No detector, dbt model or injection experiment has been run. |
| Scope | Core: UCI Default of Credit Card Clients, Feedzai BAF Base. External candidates: Santander AI Stressed German Credit Dataset (SGCD), SEC-FinTables. |
| Reproduce | `python scripts/data_intake.py status` and `python scripts/readiness_audit.py` (figures below come from `results/readiness/*.json`) |

## 1. Summary

1. **UCI Credit is ready** as the primary controlled-injection dataset. File, schema and hash are verified; the original XLS is tracked under CC BY 4.0. It contains source anomalies (undocumented codes, bills above the credit limit) that must be handled as "unknown status", not as clean ground truth.
2. **BAF Base is blocked**, not rejected. It must be downloaded manually from Kaggle (not reachable from this environment), and the CC BY-NC-ND 4.0 licence stated in the publisher datasheet needs clearance for an industry-hosted thesis. The intake check is ready to run once the file is present.
3. **SGCD is not suitable** for cell-level tabular error detection. Its shocks are applied almost entirely to a *natural-language rendering* of each record. The only change in the structured table is a null in 70 of 1,000 records, which a `not_null` test catches completely.
4. **SEC-FinTables is not suitable** as a confirmatory or held-out benchmark for CDC. It is a set of 1,000 heterogeneous, small SEC tables (median 11 rows × 5 columns) with synthetic injections and no corrected values. Its `errLoc` annotation marks every cell in a violated relationship (426 annotated cells against 77 actually changed cells where this can be checked). The injections are strongly biased towards parenthesised negative numbers (73 of 77), and the repository has no licence.
5. **The gap from pilot 4 still stands.** No examined public financial dataset has *genuine* cell errors with *independently known* locations and correct values. The two new candidates do not close it.

**Recommended minimal selection:** UCI Credit (primary) and BAF Base (secondary, conditional) for controlled experiments. There is no financial dataset for independent external validation. The external check should be limited to (a) BAF months 6–7 as an untouched later batch for false-alarm burden and (b) optionally Raha Flights as a non-financial check on genuine errors. Section 6 gives the reasoning.

## 2. What was checked and how

For every dataset, the same eight criteria were assessed. Statements are based on files inspected in this environment unless marked *not verified*.

| # | Criterion | Evidence used |
|---|---|---|
| 1 | Availability of raw data and annotations | Download at a pinned commit/hash; file counts |
| 2 | Original vs. generated/modified data | Publisher documentation; diffs between versions |
| 3 | Error locations and correct values independently known | Annotation schema; comparison with unmodified twins |
| 4 | Genuine observed vs. synthetically introduced errors | Documentation; nature of observed edits |
| 5 | Schema suitable for cell-level detectors such as CDC | Row/column counts, shared schema across records, feature types |
| 6 | Realistic conventional dbt/SQL checks definable | Documented domains, cross-field relations; failure rate on untouched data |
| 7 | Usable as held-out evaluation without modifying its original errors | Whether the benchmark can be scored as published |
| 8 | Licence, provenance, reproducibility, leakage | Licence files, datasheets, commit pins, split and artefact risks |

**Network limits in this environment (19 October 2026):** archive.ics.uci.edu, kaggle.com, arxiv.org, zenodo.org and aclanthology.org were blocked; GitHub (clone and raw files) was reachable. As a result: the UCI XLS came from the archive supplied by the researcher; the Kaggle licence notice for BAF and the SEC-FinTables paper text could **not** be read; the SGCD mother dataset (UCI Statlog German Credit) could not be downloaded for alignment.

**Label rule applied throughout:** `default payment next month` (UCI), `fraud_bool` (BAF) and `label` (SGCD, credit risk) are prediction targets. None is used, or interpretable, as a data-quality label.

## 3. Readiness matrix

| Criterion | UCI Credit | BAF Base | SGCD v0.1 | SEC-FinTables |
|---|---|---|---|---|
| 1 Availability | Yes. 30,000 × 25 XLS, sha256 pinned | **Blocked**: manual Kaggle download | Yes. 1,000 JSONL records, pinned commit | Yes. 3 × 1,000 CSV tables + ground truth, pinned commit. Only a test release; generator not published |
| 2 Original vs. modified | Original source table (2005, Taiwan) | Fully synthetic (CTGAN trained on noised real data) | Derived from UCI German Credit; structured view claimed unchanged, text view perturbed | Tables extracted from SEC 10-Q filings; ~63% of files have injected errors |
| 3 Error location / correct value known | No labels | No labels | Shocked field per record known; correct value in structured view for F2/F4; missing for F1 nulls | Relation-level `errLoc` and type known; **corrected values not published** |
| 4 Genuine vs. synthetic | Unknown source anomalies, unlabelled | Generator noise only (datasheet Q12) | Synthetic | Synthetic; the "clean" tables also contain unlabelled extraction artefacts |
| 5 Fit for CDC (cell-level) | Good: one schema, 30k rows, mixed types | Good: one schema, 1M rows, month batches | Poor: 1,000 rows; tabular errors are only nulls | Poor: 1,000 different schemas, median 11 × 5 cells, text-formatted numbers |
| 6 Realistic dbt/SQL checks | Yes, but documented domains fail on 66.9% of PAY cells | Yes, ranges and sentinels documented in datasheet | Trivial: `not_null` + `accepted_values` | Only format/null checks are generic; value checks need per-table relation extraction |
| 7 Held-out as published | Not applicable (no labels); controlled injection required | Not applicable; controlled injection required | Possible, but measures only missingness in the table | Possible, but scored at relation/table level, not at cell level |
| 8 Licence | CC BY 4.0 (UCI page; not re-read here) | CC BY-NC-ND 4.0 (datasheet); clearance required | CC BY 4.0 (dataset LICENSE) | **None declared** |
| **Verdict** | **READY: controlled** | **BLOCKED: controlled, conditional** | **NOT SUITABLE** (tabular DQ) | **NOT SUITABLE** (confirmatory); exploratory only |

## 4. Core datasets

### 4.1 UCI Default of Credit Card Clients

**Provenance and integrity.** File `data/raw/uci/default_of_credit_card_clients.xls`, sha256 `30c6be3a…0933`, extracted unchanged from the archive supplied by the researcher (archive sha256 `56c885f8…7602`, member dated 2023-05-22). It has not been byte-compared with a fresh UCI download because the site was blocked. The intake check fails if the bytes change. The licence is CC BY 4.0 according to the UCI page (recorded in the starter project; not re-read here). The file is tracked in Git with attribution in `data/raw/uci/README.md`.

**Structure.** 30,000 rows × 25 columns, all integer, no null cells, unique `ID` 1–30,000. 35 rows are exact duplicates apart from `ID`.

**Conventional checks on the untouched table** (row-level violations; from `readiness_audit.py`):

| Candidate check | Violating rows | Interpretation |
|---|---|---|
| `not_null`, `unique(ID)`, SEX ∈ {1,2}, AGE 18–100, LIMIT_BAL > 0, PAY_AMT ≥ 0 | 0 | Usable as strict tests |
| EDUCATION ∈ documented {1–4} | 345 (1.15%) | Undocumented codes 0, 5, 6 |
| MARRIAGE ∈ documented {1–3} | 54 (0.18%) | Undocumented code 0 |
| PAY_x ∈ documented {-1, 1–9} | 66.9% of PAY cells | Codes -2 and 0 dominate; the documentation is incomplete |
| any BILL_AMT < 0 | 1,930 (6.4%) | Credit balances; plausible |
| any BILL_AMT > LIMIT_BAL | 3,931 (13.1%) | Overlimit; plausible |
| any BILL_AMT > 1.5 × LIMIT_BAL | 343 (1.1%) | Candidate business rule; still fails on untouched data |

A further encoding signal for rule design: PAY code 1 occurs 3,688 times in `PAY_0` but only 0–28 times in `PAY_2`…`PAY_6`. This suggests the months are not encoded identically. Injection eligibility and `accepted_values` must therefore be defined per column, not once for all PAY fields.

**Assessment.**
- *Ground truth:* none for cell errors. Only controlled injections give labels. Flags on untouched cells are "unverified", not "false positives" (as in the proposal).
- *CDC fit:* good. One schema, enough rows for reference, calibration and test, no NaN (the CURED CDC requirement). Integer-coded categoricals must be typed explicitly (pilot 2).
- *dbt fit:* good. Rule configurations must be reported in a strict and a relaxed variant together with the failure rates above.
- *Leakage risks:* duplicate rows must be kept in one partition (group on all non-ID columns). There is no time axis, so splits are random. Rules must be specified from documentation and the reference partition only.

**Verdict: READY** for controlled experiments.

### 4.2 Feedzai BAF Base

**Provenance.** The upstream repository `feedzai/bank-account-fraud` (commit `3377cfd8`) contains the paper and datasheet but not the data. The data is only on Kaggle (`sgpjesus/bank-account-fraud-dataset-neurips-2022`), which was blocked. The datasheet (sha256 `36784673…81b0`) states:
- each record is a *synthetic* bank-account application generated by a CTGAN trained on an anonymised real dataset, with Laplacian noise added before training (Q4, privacy section);
- the only known error source is GAN generation and variant sampling (Q12);
- missing values are encoded as negative sentinels (e.g. `-1`) in six documented fields; there are no NaN (Q7, Q9);
- `month` runs 0–7, and the paper trains on months 0–5 and validates on 6–7 (Q11);
- **licence: CC BY-NC-ND 4.0** (Q44 and closing statement).

Secondary sources cite CC BY-NC-SA 4.0 for the Kaggle copy (*not verified*). The upstream code repository is Apache 2.0, which does not cover the data.

**Assessment.**
- *Ground truth:* none. `fraud_bool` is a fraud outcome.
- *Genuine errors:* none in the real-world sense. Generator artefacts may look anomalous but have no "correct value".
- *CDC fit:* good. 1M rows, one schema, mixed numeric/categorical, no NaN. Sentinels must be modelled as missing rather than as numbers.
- *dbt fit:* good. The datasheet gives admissible ranges per field; these become range tests. Some documented ranges are counter-intuitive (e.g. `velocity_6h` down to −175), so tests must follow the datasheet, not intuition.
- *Held-out:* months 6–7 form a natural later batch for the "onboard a new batch" scenario.
- *Licence risks:* NC raises the question whether a thesis hosted by an industry partner is non-commercial. ND means corrupted or adapted copies must not be shared. Keep all BAF bytes and derivatives local (enforced by `.gitignore` and a test). This is not legal advice; the supervisor or legal contact must confirm.

**Verdict: BLOCKED** until (1) the researcher downloads unmodified `Base.csv` from Kaggle and runs `verify-baf`, and (2) the licence is cleared. After that it is conditionally ready as the second controlled case.

## 5. External benchmark candidates

### 5.1 Santander AI Stressed German Credit Dataset (SGCD v0.1)

**Provenance.** `SantanderAI/sota-stressed-datasets`, commit `8403fa90` (2026-07-16), dataset version SGCD-v0.1 (released 2026-06-12). All seven dataset files are pinned by sha256 in `data/manifests/datasets.json`. Licence CC BY 4.0, with attribution to both UCI Statlog German Credit and Santander AI Lab. The generation code is not published; only the parameters are (`seed = 42`, shock probabilities per batch).

**Structure.** 1,000 records in 20 ordered batches of 50 (setup S1–S4, adaptation A1–A10, test T1–T6). Each record has a `json_view` (20 original attributes, 7 numeric + 13 coded categorical) and a `text_view` (English rendering). Shock metadata per record: `shock_semantic` F0–F4, `shock_field`, `shock_cosmetic`.

| Stage | F0 clean | F1 missingness | F2 ambiguity | F4 contradiction |
|---|---|---|---|---|
| setup | 200 | – | – | – |
| adaptation | 317 | 98 | 85 | – |
| test | 180 | 30 | 30 | 60 |

Cosmetic noise (F3): 135 records. Vague numeric wording ("roughly 13 months") appears in 198 text views.

**Key findings.**
- *Where the errors are:* per the publisher, F2, F3, F4 and the numeric noise alter **only the text view**. F4 is defined as "text states a different value than the structured view". The structured table therefore remains the clean reference rather than an error-bearing table.
- *Structured-view errors:* only F1 nulls. **Only 70 of 128 F1 records** have a null in `json_view`; in the other 58 the field is only omitted from the text. This contradicts the README ("null in the structured view").
- *Correct values:* known for F2/F4 (in `json_view`). Not contained for the 70 nulls; they could in principle be recovered from the mother dataset, but alignment was not verifiable here (UCI blocked).
- *Genuine errors:* none; all shocks are synthetic, and the mother data is used as-is.

**Assessment against the thesis design.**
- *CDC fit:* poor. 1,000 rows is at the limit of CDC's calibration advice, and the only tabular error type is a null.
- *dbt fit:* trivial. `not_null` detects 100% of the tabular F1 shocks, and `accepted_values` from the codebook covers the coded fields. F4 contradictions can only be found by parsing the text, which is a different task (document-to-record consistency, LLM robustness).
- *Held-out use:* technically possible without modification, but on the table it would only measure missingness detection. This gives no evidence on incremental value beyond conventional checks.
- *Leakage:* the mother dataset is public and widely used, so the "hidden" originals are easy to obtain. Batch order and fixed 35/15 label mixes are artificial. The data contains sensitive attributes (`personal_status_sex`, `foreign_worker`, `age`); the publisher restricts use to research.

**Verdict: NOT SUITABLE** for cell-level tabular data-quality evaluation. It may be cited as related work on robustness benchmarks. Re-assess if Santander releases a version with tabular shocks.

### 5.2 SEC-FinTables

**Provenance.** `XIEFOX/SEC-Fintables`, single commit `f82f8036` (2025-05-16, "Add files via upload"). The README contains only a title, and there is **no licence file**. The search engine lists a paper: Ke, Wu, Li, Cao, *SEC-FinTables: Evaluating Large Language Models for Detecting Logical Inconsistencies on Tabular Data*, Findings of ACL 2026. Per the search snippet, the full benchmark has 103,395 table instances (*not verified*; paper text blocked). The repository contains only 3 × 1,000 test tables, ground-truth JSON, LLM outputs for 8 models, an evaluation script and HTML-to-CSV extraction scripts. **The error generator and any training split are not published.** The data tree is pinned by an aggregate sha256 (`24c7c7a7…e899`).

**Structure.** Folders `1000test_1%`, `1000test_10%`, `1000test_50%` contain the **same 1,000 table IDs** (08001–09000). The meaning of the percentages is not documented in the repository. Per folder, ~63% of files carry an `_err_<TYPES>_1` suffix with error types `VAL`, `MISS`, `FMT` and combinations. Each ground-truth entry has `errNum`, `errLoc` (row label + column index), `errType` and `missNum`, with no corrected value. Tables are small and heterogeneous: median 11 rows (max 79) and 5 columns (max 16), and numbers are text (`$(1,704)`, `—`).

**Direct check of the annotations.** In 75 table versions, an `_err_` file has an unmodified twin in another folder. Comparing these cell by cell gives:

| Measure | Value |
|---|---|
| Cells actually changed | 77 (71 versions: 1 cell, 3 versions: 2 cells) |
| Changed cells inside `errLoc` | 77 of 77 |
| Cells listed in `errLoc` for those versions | 426 (≈5.5 per changed cell) |
| `_err_` file identical to its clean twin | 1 (annotated as `MISS_FMT` with 4 locations) |
| Changed cells that were parenthesised negatives in the original | 73 of 77 (95%) |
| Tables where all folders corrupted the *same* cells | 31 of 32 checkable |
| Observed edit types | blanking a cell (`MISS`), format change such as `(1)` → `(1)%`, `$(354)` → `$(354).00`, `$(287)` → `$,(,287,)` (`FMT`), changed digits (`VAL`) |

Further annotation inconsistencies: per folder, 1 file named `_err_` has `errNum = 0`, and in the 1% folder one unsuffixed file has `errNum > 0`. Among the 369 unsuffixed ("clean") tables in the 1% folder are unlabelled extraction artefacts: 22 with unbalanced parentheses (e.g. `(6`), 44 with a cell longer than 200 characters (whole table text in one cell), and 148 with duplicate row labels.

**Assessment against the thesis design.**
- *Error locations:* `errLoc` marks the cells of the violated arithmetic relationship, not the modified cell. Cell-level precision/recall against it would penalise a detector that finds exactly the modified cell.
- *Correct values:* not published, and not independently recoverable. There is no mapping from table ID to company, filing or period, so EDGAR re-verification is not feasible. Clean twins exist for only 43 tables.
- *Genuine errors:* the injections are synthetic. The genuine extraction artefacts in "clean" tables are unlabelled and would be scored as false positives.
- *CDC fit:* poor. CDC learns cross-column structure over many rows of one schema; here each table has its own schema and about 55 cells.
- *dbt fit:* generic checks can be written after unpivoting to `(table_id, row_label, col_idx, raw_value)`: `not_null` on non-header cells and a regex for accepted numeric formats. These would likely catch most `MISS` and `FMT` edits (not measured). `VAL` errors require a per-table "total = sum of components" relationship, which cannot be specified as a realistic, reusable dbt test without per-table semantics.
- *Held-out use:* as published, it scores table-level and relation-level detection by LLMs. Using it for CDC would require re-annotation to the changed cell, which modifies the benchmark's ground truth.
- *Leakage and validity:* the 95% concentration on parenthesised negatives is a target-selection artefact a detector can exploit. Folders are not independent replicates (same tables, mostly same target cells). The source filings are public and likely in LLM pretraining corpora (relevant for LLM baselines, not CDC). Without a licence, the tables and derivatives must not be redistributed; use for private evaluation needs confirmation.

**Verdict: NOT SUITABLE** as a confirmatory or held-out benchmark for this thesis. At most it is an exploratory illustration that format and missing-value injections are caught by conventional checks, labelled as such, if a licence or author permission is obtained. It does not provide genuine financial cell errors.

## 6. Recommendation: minimal final dataset selection

### Controlled experiments (injected errors, own generator, labels by construction)

| Dataset | Role | Split | Condition |
|---|---|---|---|
| **UCI Credit** | Primary | 60/20/20 reference/selection/test, random, group-aware on duplicate rows; fixed seed | Ready |
| **BAF Base** | Secondary financial case | Months 0–5 reference and selection; months 6–7 final test | Kaggle download + `verify-baf` + licence clearance |

In both, injections only touch cells with an explicit eligibility rule, and every edit is logged with seed and original value. Unmodified source anomalies keep the status "unknown", not "clean".

### Independent external validation

No examined financial dataset meets all three requirements: genuine errors, independently known location and correct value, and a CDC-compatible schema. The thesis should state this as a limitation rather than fill the slot with a weak benchmark. The minimal defensible external evidence is:

1. **Untouched-batch validation (financial, no injection):** BAF months 6–7 scored as published. This measures alert burden and rule failure rates on a later, unseen batch. It does not measure detection, because there are no error labels.
2. **Genuine-error check (non-financial, optional):** Raha Flights, as already decided, presented only as an implementation-generality check.

**Excluded:** SGCD (text-view shocks; table errors trivial) and SEC-FinTables (relation-level labels without corrected values, heterogeneous schemas, target-selection bias, no licence). TableEG and AuditBench remain excluded (decision log).

## 7. Blockers and actions

| # | Action | Owner | Blocks |
|---|---|---|---|
| 1 | Download unmodified BAF `Base.csv` from the official Kaggle page; record version, licence text, date. Place it at `data/raw/baf/Base.csv`, run `verify-baf`, pin the sha256 in `datasets.json` | Researcher | BAF experiments |
| 2 | Confirm whether CC BY-NC-ND 4.0 permits the thesis use (industry host; local corrupted copies) | Supervisor / legal contact | BAF experiments |
| 3 | On an unrestricted network, run `download-uci` in a clean clone and confirm the sha256 matches the tracked file | Researcher | Nothing (provenance hardening) |
| 4 | Optional: read the SEC-FinTables paper to confirm the meaning of 1/10/50% and the injection procedure; ask the authors about a licence | Researcher | Nothing (only if exploratory use is wanted) |
| 5 | Review this report and the recommended selection before Stage 1 (dbt baseline) starts | Supervisor | Stage 1 |

## 8. Reproduction

```bash
python -m pip install -r requirements-data.txt
python scripts/data_intake.py verify-uci            # tracked XLS; or download-uci / import-uci <zip>
python scripts/data_intake.py fetch-sgcd            # pinned commit, raw.githubusercontent.com
python scripts/data_intake.py fetch-secfintables    # pinned commit, git
python scripts/data_intake.py verify-external
python scripts/data_intake.py verify-baf            # after manual Kaggle download
python scripts/readiness_audit.py                   # writes results/readiness/*.json
python -m pytest -q
```

`verify-all` covers only the two core datasets and currently fails by design because BAF is missing.

## 9. Sources

- UCI dataset page, DOI 10.24432/C55S3H: https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients (blocked here; licence taken from the starter documentation)
- Feedzai BAF repository and datasheet (commit `3377cfd8`): https://github.com/feedzai/bank-account-fraud; Kaggle: https://www.kaggle.com/datasets/sgpjesus/bank-account-fraud-dataset-neurips-2022 (blocked here)
- Jesus et al. (2022), *Turning the Tables*, NeurIPS Datasets & Benchmarks: https://arxiv.org/abs/2211.13358
- Santander AI Lab, Stressed SOTA Datasets (commit `8403fa90`): https://github.com/SantanderAI/sota-stressed-datasets
- UCI Statlog German Credit (SGCD mother dataset): https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data
- SEC-FinTables repository (commit `f82f8036`): https://github.com/XIEFOX/SEC-Fintables
- Ke et al. (2026), *SEC-FinTables*, Findings of ACL (listing only): https://preview.aclanthology.org/ingest-acl/2026.findings-acl.764/
- Earlier pilots: `docs/research/pilot_summaries/` and `docs/research/decision_log.md`
