# External benchmark candidates (not committed)

Fetched at pinned upstream commits by `scripts/data_intake.py`; expected hashes in
`data/manifests/datasets.json`. Contents of this folder are ignored by Git.

| Folder | Fetch | Verify | Why not committed |
|---|---|---|---|
| `sgcd/` | `python scripts/data_intake.py fetch-sgcd` | `verify-sgcd` | CC BY 4.0 would allow it, but a pinned fetch keeps provenance unambiguous and the repo lean |
| `sec_fintables/` | `python scripts/data_intake.py fetch-secfintables` | `verify-secfintables` | No licence declared upstream: do not redistribute tables or derivatives |

See `docs/research/dataset_readiness_report.md` for the assessment of both. Neither is
part of the recommended confirmatory dataset selection.
