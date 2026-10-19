# Manifests

- `datasets.json` (tracked): expected source, pinned commit, licence, SHA-256 and Git policy per dataset.
  `scripts/data_intake.py` verifies local files against it.
- `*.local.json` (ignored): written by each `verify-*` command with the observed hash, counts and
  timestamp on the machine that ran it. Not committed because BAF results describe a local-only file.

After downloading BAF Base.csv, run `verify-baf` and copy the observed SHA-256 into
`datasets.json` (`baf_base.sha256`) so later runs detect a different file version.
