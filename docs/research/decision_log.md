# Scope and dataset decisions — 19 October 2026

This record summarizes research decisions. See the full pilot summaries for supporting detail. It does not imply that the newer strong baseline has already been run.

## Scope

The previous primary hypothesis — that mechanism-aware detector selection improves detector choice — was not supported by the small technical pilot. ECAR-only and multi-mechanism selection chose the same detector in 15/18 cases, and the maximum F1 regret was 0.013. CDC generated many additional flags on uncorrupted cells; the comparison relied on weak conventional checks. Reframing the study towards the incremental value and robustness of ML beyond realistic conventional controls is warranted.

## Confirmed prior observations

- Earlier pilot: injection, CDC, LUCARIO, and selection pipeline were technically reproducible in one setting.
- Data study: TableEG Credit and Marketing clean/dirty differences are not defensible independent cell-error labels.
- Later finance-oriented feasibility work: UCI Credit is a usable primary simulation source, but not independently certified clean. BAF Base appears useful for month-based batches but is not yet locally acquired/validated here; license confirmation is required.
- AuditBench, as examined, does not provide a defensible cell-level banking benchmark for this design.
- Pilot 4 was a **feasibility/data-use-case assessment only**; it did not execute the new strong dbt baseline or a fair CDC-versus-dbt comparison.

## Immediate next scientific questions

1. What robust, justified dbt and statistical checks detect nontrivial synthetic errors on UCI Credit?
2. At a fixed review budget, does CDC detect meaningfully more injected errors that these controls miss, and at what extra false-alarm cost?
3. Do the conclusions change with corruption type, ECAR/EAR/ENAR placement, rate, random seed, or a second financial dataset?
4. Is a reproducible recommendation (including 'no additional detector' or 'insufficient evidence') warranted?

## Data integrity and evaluation constraints

- Outcome/fraud labels are **not** cell-error labels.
- Existing source anomalies must not be silently scored as clean ground truth.
- Do not write scenario-specific controls based on held-out injected errors.
- Separate test-set metrics from tuning, and do not artificially strengthen an AI result through weak rules or selective reporting of columns.
- Source semantics and business constraints should be independently reviewed before presenting a simulated case as representative of banking work.

# Dataset readiness decisions — 19 October 2026 (readiness study)

Full evidence: `docs/research/dataset_readiness_report.md`.

- **UCI Credit: accepted** for controlled experiments. Original XLS tracked with sha256 pin. Candidate checks already fail on untouched data (66.9% of PAY cells outside the documented codes; 345 rows with undocumented EDUCATION; 343 rows with a bill above 1.5 × limit); these cells stay "unknown status". 35 duplicate rows (excluding ID) must stay in one split partition.
- **BAF Base: blocked**, not rejected. Waiting on manual Kaggle download and clearance of CC BY-NC-ND 4.0 (publisher datasheet). Planned role: second controlled case, months 6–7 as untouched later batch.
- **Santander SGCD v0.1: rejected** for tabular cell-level evaluation. Shocks F2–F4 alter only the text rendering; the structured table carries only F1 nulls (70 records), which `not_null` catches entirely.
- **SEC-FinTables: rejected** as confirmatory/held-out benchmark. No corrected values; `errLoc` marks whole violated relations (426 annotated vs 77 changed cells where verifiable); 73 of 77 injected cells were parenthesised negatives; heterogeneous small tables; no licence.
- **External validation:** no financial benchmark with genuine, independently corrected cell errors exists among the candidates. Use BAF months 6–7 (untouched) for alert burden and, optionally, Raha Flights as a non-financial genuine-error check. State the gap as a limitation.
