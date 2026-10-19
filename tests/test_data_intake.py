import json
import re
import shutil
import subprocess
import zipfile

import pytest

from scripts import data_intake


def test_expected_uci_schema_length_and_identity():
    assert len(data_intake.UCI_COLUMNS) == 25
    assert data_intake.UCI_COLUMNS[0] == "ID"
    assert data_intake.UCI_COLUMNS[1] == "LIMIT_BAL"
    assert data_intake.UCI_COLUMNS[-1] == "default payment next month"


def test_hash_function(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_bytes(b"abc")
    assert data_intake.sha256(test_file) == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_tree_hash_is_order_independent_and_content_sensitive(tmp_path):
    for name, content in (("b/2.csv", b"x"), ("a/1.csv", b"y")):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_bytes(content)
    first = data_intake.tree_sha256(tmp_path, ["a", "b"])
    assert first == data_intake.tree_sha256(tmp_path, ["b", "a"])
    (tmp_path / "a/1.csv").write_bytes(b"z")
    assert first != data_intake.tree_sha256(tmp_path, ["a", "b"])


def test_manifest_lists_all_datasets_with_pins():
    manifest = json.loads(data_intake.EXPECTED_MANIFEST.read_text(encoding="utf-8"))["datasets"]
    assert set(manifest) == {"uci_credit", "baf_base", "sgcd", "sec_fintables"}
    hexdigest = re.compile(r"^[0-9a-f]{64}$")
    assert hexdigest.match(manifest["uci_credit"]["sha256"])
    assert manifest["baf_base"]["sha256"] is None or hexdigest.match(manifest["baf_base"]["sha256"])
    assert all(hexdigest.match(d) for d in manifest["sgcd"]["files"].values())
    assert hexdigest.match(manifest["sec_fintables"]["data_tree_sha256"])
    for key in ("sgcd", "sec_fintables"):
        assert re.match(r"^[0-9a-f]{40}$", manifest[key]["commit"])
    for entry in manifest.values():
        assert entry["license"] and entry["git_policy"]


def test_uci_archive_extraction_keeps_bytes(tmp_path, monkeypatch):
    payload = b"original xls bytes"
    archive = tmp_path / "uci.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr(data_intake.UCI_ARCHIVE_MEMBER, payload)
    target = tmp_path / "raw/uci/default_of_credit_card_clients.xls"
    monkeypatch.setattr(data_intake, "UCI_XLS", target)
    data_intake.import_uci(archive)
    assert target.read_bytes() == payload


def test_uci_archive_without_xls_is_rejected(tmp_path, monkeypatch):
    archive = tmp_path / "other.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("readme.txt", b"nothing")
    monkeypatch.setattr(data_intake, "UCI_XLS", tmp_path / "x.xls")
    with pytest.raises(ValueError):
        data_intake.import_uci(archive)
    assert not (tmp_path / "x.xls").exists()


def test_restricted_and_derived_data_are_gitignored():
    ignored = (data_intake.ROOT / ".gitignore").read_text()
    for pattern in ("data/raw/baf/*", "data/external/*", "data/processed/*", "results/", "data/manifests/*.local.json"):
        assert pattern in ignored


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_no_restricted_files_are_tracked():
    result = subprocess.run(["git", "-C", str(data_intake.ROOT), "ls-files"], capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip("not a git checkout")
    tracked = result.stdout.splitlines()
    allowed_readmes = {"data/raw/baf/README.md", "data/external/README.md", "data/processed/README.md"}
    for path in tracked:
        if path.startswith(("data/raw/baf/", "data/external/", "data/processed/", "results/")):
            assert path in allowed_readmes, path
        assert not path.endswith(".local.json"), path


def test_source_urls_point_to_upstream_research_sources():
    assert data_intake.UCI_URL.startswith("https://archive.ics.uci.edu/")
    assert data_intake.SGCD_RAW_URL.startswith("https://raw.githubusercontent.com/SantanderAI/")
    assert data_intake.expected("sec_fintables")["source"] == "https://github.com/XIEFOX/SEC-Fintables"
