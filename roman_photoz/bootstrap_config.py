from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class BootstrapConfigError(ValueError):
    """Raised when bootstrap configuration is invalid."""


ALLOWED_PARS_KEYS = {
    "PARS_VERSION",
    "DATA_ROOT",
    "LEPHAREDIR",
    "LEPHAREWORK",
    "INFORMER_MODEL_PATH",
    "ENV_FILE",
    "NOBJ",
    "SIMULATED_CATALOG_FILENAME",
    "BUILD_MODEL",
    "CLEANUP_MODE",
    "FORCE_REFRESH",
    "VERIFY_ASSETS",
    "PYTHON_RUNNER",
}

BOOL_KEYS = {"BUILD_MODEL", "FORCE_REFRESH", "VERIFY_ASSETS"}
INT_KEYS = {"NOBJ"}
STR_KEYS = ALLOWED_PARS_KEYS - BOOL_KEYS - INT_KEYS

DEFAULTS: dict[str, Any] = {
    "PARS_VERSION": "1",
    "DATA_ROOT": ".",
    "NOBJ": 1000,
    "SIMULATED_CATALOG_FILENAME": "roman_simulated_catalog.parquet",
    "BUILD_MODEL": True,
    "CLEANUP_MODE": "full",
    "FORCE_REFRESH": False,
    "VERIFY_ASSETS": True,
    "PYTHON_RUNNER": "uv run",
}

OUTPUT_ORDER = [
    "PARS_SOURCE",
    "PARS_VERSION",
    "DATA_ROOT",
    "LEPHAREDIR",
    "LEPHAREWORK",
    "INFORMER_MODEL_PATH",
    "ENV_FILE",
    "NOBJ",
    "SIMULATED_CATALOG_FILENAME",
    "BUILD_MODEL",
    "CLEANUP_MODE",
    "FORCE_REFRESH",
    "VERIFY_ASSETS",
    "PYTHON_RUNNER",
]


def _strip_matching_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _parse_bool(raw_value: Any, key: str) -> bool:
    value = str(raw_value).strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise BootstrapConfigError(
        f"Invalid boolean value for {key}: {raw_value!r}. Expected true/false."
    )


def _parse_int(raw_value: Any, key: str) -> int:
    try:
        value = int(str(raw_value).strip())
    except ValueError as exc:
        raise BootstrapConfigError(
            f"Invalid integer value for {key}: {raw_value!r}."
        ) from exc
    return value


def _resolve_path(value: str, base_dir: Path) -> Path:
    path = Path(_strip_matching_quotes(value)).expanduser()
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    else:
        path = path.resolve()
    return path


def _validate_cleanup_mode(value: str) -> str:
    normalized = value.strip().lower()
    allowed = {"trimmed", "full", "none"}
    if normalized not in allowed:
        raise BootstrapConfigError(
            f"Invalid CLEANUP_MODE {value!r}. Expected one of: {sorted(allowed)}."
        )
    return normalized


def parse_pars_file(pars_file: str | Path) -> dict[str, str]:
    path = Path(pars_file)
    if not path.exists():
        raise BootstrapConfigError(f"Pars file not found: {path}")

    parsed: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text().splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            raise BootstrapConfigError(
                f"Invalid line {line_number} in {path}: expected KEY=VALUE format."
            )
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise BootstrapConfigError(
                f"Invalid line {line_number} in {path}: empty key is not allowed."
            )
        if key in parsed:
            raise BootstrapConfigError(
                f"Duplicate key {key!r} found in {path} at line {line_number}."
            )
        parsed[key] = value
    return parsed


def _apply_raw_config(config: dict[str, Any], raw_values: dict[str, Any]) -> None:
    unknown_keys = sorted(set(raw_values) - ALLOWED_PARS_KEYS)
    if unknown_keys:
        raise BootstrapConfigError(
            f"Unknown key(s) in bootstrap pars: {', '.join(unknown_keys)}."
        )

    for key, raw_value in raw_values.items():
        if key in BOOL_KEYS:
            config[key] = _parse_bool(raw_value, key)
        elif key in INT_KEYS:
            config[key] = _parse_int(raw_value, key)
        elif key in STR_KEYS:
            config[key] = _strip_matching_quotes(str(raw_value).strip())
        else:
            raise BootstrapConfigError(f"Unhandled config key: {key}")


def resolve_bootstrap_config(
    *,
    script_dir: str | Path,
    pars_file: str | Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    script_dir = Path(script_dir).resolve()
    config = dict(DEFAULTS)
    config["PARS_SOURCE"] = "defaults"

    if pars_file is not None:
        raw_pars = parse_pars_file(pars_file)
        if "PARS_VERSION" not in raw_pars:
            raise BootstrapConfigError(
                f"Pars file {pars_file} must define PARS_VERSION=1."
            )
        _apply_raw_config(config, raw_pars)
        if str(config["PARS_VERSION"]) != "1":
            raise BootstrapConfigError(
                f"Unsupported PARS_VERSION {config['PARS_VERSION']!r}. Only '1' is supported."
            )
        config["PARS_SOURCE"] = str(Path(pars_file).resolve())

    if cli_overrides:
        _apply_raw_config(config, cli_overrides)

    nobj = int(config["NOBJ"])
    if nobj <= 0:
        raise BootstrapConfigError("NOBJ must be a positive integer.")

    simulated_catalog_filename = str(config["SIMULATED_CATALOG_FILENAME"]).strip()
    if not simulated_catalog_filename:
        raise BootstrapConfigError("SIMULATED_CATALOG_FILENAME cannot be empty.")
    if Path(simulated_catalog_filename).name != simulated_catalog_filename:
        raise BootstrapConfigError(
            "SIMULATED_CATALOG_FILENAME must be a filename, not a path."
        )

    cleanup_mode = _validate_cleanup_mode(str(config["CLEANUP_MODE"]))

    data_root = _resolve_path(str(config["DATA_ROOT"]), script_dir)
    if str(config.get("LEPHAREDIR", "")).strip():
        lepharedir = _resolve_path(str(config["LEPHAREDIR"]), script_dir)
    else:
        lepharedir = (data_root / "lephare_data").resolve()

    if str(config.get("LEPHAREWORK", "")).strip():
        lepharework = _resolve_path(str(config["LEPHAREWORK"]), script_dir)
    else:
        lepharework = (data_root / "lephare_work").resolve()

    if str(config.get("INFORMER_MODEL_PATH", "")).strip():
        informer_model_path = _resolve_path(str(config["INFORMER_MODEL_PATH"]), script_dir)
    else:
        informer_model_path = lepharework

    if str(config.get("ENV_FILE", "")).strip():
        env_file = _resolve_path(str(config["ENV_FILE"]), script_dir)
    else:
        env_file = (script_dir / ".env").resolve()

    python_runner = str(config.get("PYTHON_RUNNER", "uv run")).strip()
    if not python_runner:
        raise BootstrapConfigError("PYTHON_RUNNER cannot be empty.")

    return {
        "PARS_SOURCE": config["PARS_SOURCE"],
        "PARS_VERSION": "1",
        "DATA_ROOT": data_root.as_posix(),
        "LEPHAREDIR": lepharedir.as_posix(),
        "LEPHAREWORK": lepharework.as_posix(),
        "INFORMER_MODEL_PATH": informer_model_path.as_posix(),
        "ENV_FILE": env_file.as_posix(),
        "NOBJ": nobj,
        "SIMULATED_CATALOG_FILENAME": simulated_catalog_filename,
        "BUILD_MODEL": bool(config["BUILD_MODEL"]),
        "CLEANUP_MODE": cleanup_mode,
        "FORCE_REFRESH": bool(config["FORCE_REFRESH"]),
        "VERIFY_ASSETS": bool(config["VERIFY_ASSETS"]),
        "PYTHON_RUNNER": python_runner,
    }


def format_config_as_kv_lines(config: dict[str, Any]) -> str:
    lines: list[str] = []
    for key in OUTPUT_ORDER:
        value = config[key]
        if isinstance(value, bool):
            value_str = "true" if value else "false"
        else:
            value_str = str(value)
        lines.append(f"{key}={value_str}")
    return "\n".join(lines)


def format_config_as_json(config: dict[str, Any]) -> str:
    """Serialize resolved config as a single-line JSON object.

    JSON is the canonical machine-readable interchange format between this
    module and bootstrap_roman_photoz.sh: it avoids the ambiguity of
    delimiter-based KEY=VALUE parsing (e.g. values containing '=' or stray
    stdout output) that a line-oriented format is vulnerable to.
    """
    ordered = {key: config[key] for key in OUTPUT_ORDER}
    return json.dumps(ordered)


def _parse_cli_overrides(raw_overrides: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for raw_item in raw_overrides:
        if "=" not in raw_item:
            raise BootstrapConfigError(
                f"Invalid --override value {raw_item!r}. Expected KEY=VALUE."
            )
        key, value = raw_item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise BootstrapConfigError(
                f"Invalid --override value {raw_item!r}. Empty key is not allowed."
            )
        overrides[key] = value
    return overrides


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve and validate bootstrap configuration from pars + CLI overrides."
    )
    parser.add_argument(
        "--script-dir",
        type=str,
        required=True,
        help="Directory where bootstrap_roman_photoz.sh lives.",
    )
    parser.add_argument(
        "--pars-file",
        type=str,
        default=None,
        help="Optional path to pars file.",
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        help="Override in KEY=VALUE format. May be provided multiple times.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "kv"],
        default="json",
        help="Output format for the resolved configuration (default: json).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    overrides = _parse_cli_overrides(args.override)
    config = resolve_bootstrap_config(
        script_dir=args.script_dir,
        pars_file=args.pars_file,
        cli_overrides=overrides,
    )
    if args.format == "json":
        print(format_config_as_json(config))
    else:
        print(format_config_as_kv_lines(config))


if __name__ == "__main__":
    main()
