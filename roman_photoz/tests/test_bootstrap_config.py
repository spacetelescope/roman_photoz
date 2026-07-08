import json
from pathlib import Path

import pytest

from roman_photoz.bootstrap_config import (
    DEFAULTS,
    BootstrapConfigError,
    format_config_as_json,
    format_config_as_kv_lines,
    parse_pars_file,
    resolve_bootstrap_config,
)


def _write_pars(tmp_path: Path, content: str, name: str = "bootstrap.pars") -> Path:
    path = tmp_path / name
    path.write_text(content)
    return path


def test_parse_pars_file_skips_comments_and_blank_lines(tmp_path):
    pars_file = _write_pars(
        tmp_path,
        """
# comment

PARS_VERSION=1
DATA_ROOT=.
BUILD_MODEL=true
""",
    )

    parsed = parse_pars_file(pars_file)
    assert parsed["PARS_VERSION"] == "1"
    assert parsed["DATA_ROOT"] == "."
    assert parsed["BUILD_MODEL"] == "true"


def test_parse_pars_file_rejects_duplicate_key(tmp_path):
    pars_file = _write_pars(
        tmp_path,
        """
PARS_VERSION=1
DATA_ROOT=.
DATA_ROOT=/tmp/other
""",
    )

    with pytest.raises(BootstrapConfigError, match="Duplicate key"):
        parse_pars_file(pars_file)


def test_resolve_bootstrap_config_requires_pars_version(tmp_path):
    pars_file = _write_pars(tmp_path, "DATA_ROOT=.\n")

    with pytest.raises(BootstrapConfigError, match="must define PARS_VERSION=1"):
        resolve_bootstrap_config(script_dir=tmp_path, pars_file=pars_file)


def test_resolve_bootstrap_config_rejects_unknown_key(tmp_path):
    pars_file = _write_pars(
        tmp_path,
        """
PARS_VERSION=1
DATA_ROOT=.
UNKNOWN_KEY=abc
""",
    )

    with pytest.raises(BootstrapConfigError, match="Unknown key"):
        resolve_bootstrap_config(script_dir=tmp_path, pars_file=pars_file)


def test_resolve_bootstrap_config_derives_paths_from_data_root(tmp_path):
    data_root = tmp_path / "data-root"
    pars_file = _write_pars(
        tmp_path,
        f"""
PARS_VERSION=1
DATA_ROOT={data_root.as_posix()}
""",
    )

    config = resolve_bootstrap_config(script_dir=tmp_path, pars_file=pars_file)
    assert config["DATA_ROOT"] == data_root.resolve().as_posix()
    assert config["LEPHAREDIR"] == (data_root / "lephare_data").resolve().as_posix()
    assert config["LEPHAREWORK"] == (data_root / "lephare_work").resolve().as_posix()


def test_resolve_bootstrap_config_cli_overrides_take_precedence(tmp_path):
    pars_file = _write_pars(
        tmp_path,
        """
PARS_VERSION=1
DATA_ROOT=.
NOBJ=1000
BUILD_MODEL=true
""",
    )

    config = resolve_bootstrap_config(
        script_dir=tmp_path,
        pars_file=pars_file,
        cli_overrides={
            "NOBJ": "42",
            "BUILD_MODEL": "false",
            "SIMULATED_CATALOG_FILENAME": "custom_catalog.parquet",
        },
    )

    assert config["NOBJ"] == 42
    assert config["BUILD_MODEL"] is False
    assert config["SIMULATED_CATALOG_FILENAME"] == "custom_catalog.parquet"


@pytest.mark.parametrize("cleanup_mode", ["trimmed", "full", "none"])
def test_resolve_bootstrap_config_accepts_supported_cleanup_modes(tmp_path, cleanup_mode):
    pars_file = _write_pars(
        tmp_path,
        f"""
PARS_VERSION=1
DATA_ROOT=.
CLEANUP_MODE={cleanup_mode}
""",
    )
    config = resolve_bootstrap_config(script_dir=tmp_path, pars_file=pars_file)
    assert config["CLEANUP_MODE"] == cleanup_mode


def test_resolve_bootstrap_config_rejects_invalid_cleanup_mode(tmp_path):
    pars_file = _write_pars(
        tmp_path,
        """
PARS_VERSION=1
DATA_ROOT=.
CLEANUP_MODE=aggressive
""",
    )
    with pytest.raises(BootstrapConfigError, match="Invalid CLEANUP_MODE"):
        resolve_bootstrap_config(script_dir=tmp_path, pars_file=pars_file)


def test_resolve_bootstrap_config_defaults_work_without_pars_file(tmp_path):
    config = resolve_bootstrap_config(script_dir=tmp_path, pars_file=None)
    assert config["DATA_ROOT"] == tmp_path.resolve().as_posix()
    assert config["PARS_SOURCE"] == "defaults"
    assert config["BUILD_MODEL"] is True
    # CLEANUP_MODE defaults to "full" (not "trimmed") so first-time users
    # don't silently lose LEPHAREDIR contents on their very first run.
    assert config["CLEANUP_MODE"] == "full"


def test_format_config_as_kv_lines_serializes_expected_keys(tmp_path):
    config = resolve_bootstrap_config(script_dir=tmp_path)
    kv = format_config_as_kv_lines(config).splitlines()

    assert any(line.startswith("PARS_SOURCE=") for line in kv)
    assert any(line.startswith("LEPHAREDIR=") for line in kv)
    assert any(line == "BUILD_MODEL=true" for line in kv)


def test_format_config_as_json_serializes_expected_keys(tmp_path):
    config = resolve_bootstrap_config(script_dir=tmp_path)
    payload = json.loads(format_config_as_json(config))

    assert payload["PARS_SOURCE"] == "defaults"
    assert payload["BUILD_MODEL"] is True
    assert payload["CLEANUP_MODE"] == "full"
    assert "LEPHAREDIR" in payload


def test_shipped_pars_template_matches_defaults():
    """Guard against the shipped .pars template silently drifting from DEFAULTS.

    The template documents defaults in comments for users; if DEFAULTS ever
    changes without updating the template (or vice versa), this test fails.
    """
    template_path = (
        Path(__file__).resolve().parents[2] / "bootstrap_roman_photoz.pars"
    )
    raw = parse_pars_file(template_path)

    # Paths (LEPHAREDIR/LEPHAREWORK/INFORMER_MODEL_PATH/ENV_FILE) are
    # intentionally left commented out in the template since they are
    # derived from DATA_ROOT, so only compare keys the template sets.
    for key, raw_value in raw.items():
        if key == "PARS_VERSION":
            continue
        default_value = DEFAULTS.get(key)
        assert default_value is not None, f"{key} has no corresponding DEFAULTS entry"
        assert str(raw_value).strip().lower() == str(default_value).strip().lower(), (
            f"Shipped .pars value for {key} ({raw_value!r}) does not match "
            f"DEFAULTS ({default_value!r})."
        )
