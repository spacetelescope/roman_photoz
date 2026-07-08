#!/usr/bin/env bash
#
# Bootstrap script for roman-photoz.
#
# This script:
#   1. Resolves bootstrap configuration from pars + CLI overrides
#   2. Generates a .env runtime file from the resolved configuration
#   3. Downloads only the auxiliary data required by the Roman config
#   4. Optionally builds the Roman model (informer stage)
#   5. Applies cleanup policy and verifies required assets
#
# Usage:
#   bash bootstrap_roman_photoz.sh [--pars-file FILE] [overrides]
#
# Options:
#   --pars-file FILE                  Path to bootstrap pars file (default: bootstrap_roman_photoz.pars if present)
#   --nobj N                          Number of objects in simulated catalog
#   --simulated-catalog-filename FILE Simulated catalog filename
#   --data-root DIR                   Base directory used to derive LEPHAREDIR/LEPHAREWORK
#   --lepharedir DIR                  Explicit LEPHAREDIR override
#   --lepharework DIR                 Explicit LEPHAREWORK override
#   --informer-model-path DIR         Explicit INFORMER_MODEL_PATH override
#   --env-file FILE                   Path to generated .env file
#   --cleanup-mode MODE               Cleanup policy:
#                                     trimmed = remove intermediates + trim LEPHAREDIR to estimator essentials
#                                     full    = remove intermediates only, keep full LEPHAREDIR tree
#                                     none    = keep all generated intermediates and LEPHAREDIR contents
#   --build-model                     Build the Roman model (informer stage); omit to skip
#   --force-refresh                   Force refresh model/lib_mag assets; omit to disable
#   --verify-assets                   Validate required artifacts after bootstrap; omit to skip
#   --python-runner CMD               Runner used for python/CLI invocation (e.g. 'uv run')
#   --dry-run                         Show resolved configuration/actions without mutating files
#   -h, --help                        Show this help text
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEFAULT_PARS_FILE="${SCRIPT_DIR}/bootstrap_roman_photoz.pars"

print_help() {
  cat <<'EOF'
Bootstrap script for roman-photoz.

Usage:
  bash bootstrap_roman_photoz.sh [--pars-file FILE] [overrides]

Options:
  --pars-file FILE                  Path to bootstrap pars file (default: bootstrap_roman_photoz.pars if present)
  --nobj N                          Number of objects in simulated catalog
  --simulated-catalog-filename FILE Simulated catalog filename
  --data-root DIR                   Base directory used to derive LEPHAREDIR/LEPHAREWORK
  --lepharedir DIR                  Explicit LEPHAREDIR override
  --lepharework DIR                 Explicit LEPHAREWORK override
  --informer-model-path DIR         Explicit INFORMER_MODEL_PATH override
  --env-file FILE                   Path to generated .env file
  --cleanup-mode MODE               Cleanup policy:
                                    trimmed = remove intermediates + trim LEPHAREDIR to estimator essentials
                                    full    = remove intermediates only, keep full LEPHAREDIR tree
                                    none    = keep all generated intermediates and LEPHAREDIR contents
  --build-model                     Build the Roman model (informer stage); omit to skip
  --force-refresh                   Force refresh model/lib_mag assets; omit to disable
  --verify-assets                   Validate required artifacts after bootstrap; omit to skip
  --python-runner CMD               Runner used for python/CLI invocation (e.g. 'uv run')
  --dry-run                         Show resolved configuration/actions without mutating files
  -h, --help                        Show this help text
EOF
}

to_runner_array() {
  local runner="$1"
  if [[ -z "${runner// }" ]]; then
    echo "PYTHON_RUNNER cannot be empty." >&2
    exit 1
  fi
  read -r -a PYTHON_RUNNER_CMD <<<"${runner}"
  if [[ ${#PYTHON_RUNNER_CMD[@]} -eq 0 ]]; then
    echo "Unable to parse PYTHON_RUNNER command: ${runner}" >&2
    exit 1
  fi
  if ! command -v "${PYTHON_RUNNER_CMD[0]}" >/dev/null 2>&1; then
    echo "PYTHON_RUNNER command '${PYTHON_RUNNER_CMD[0]}' was not found on PATH." >&2
    echo "Install it, or set PYTHON_RUNNER (e.g. --python-runner python or PYTHON_RUNNER=python in the pars file)." >&2
    exit 1
  fi
}

run_cmd() {
  local printable
  printable="$(printf '%q ' "$@")"
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "DRY-RUN: ${printable}"
    return
  fi
  "$@"
}

stage_is_complete() {
  local stage="$1"
  [[ -f "${STATE_FILE}" ]] && grep -qx "${stage}" "${STATE_FILE}" 2>/dev/null
}

mark_stage_complete() {
  local stage="$1"
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "DRY-RUN: would mark stage '${stage}' complete in ${STATE_FILE}"
    return
  fi
  mkdir -p "$(dirname "${STATE_FILE}")"
  stage_is_complete "${stage}" || echo "${stage}" >>"${STATE_FILE}"
}

clear_stage() {
  local stage="$1"
  [[ -f "${STATE_FILE}" ]] || return 0
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "DRY-RUN: would clear stage '${stage}' from ${STATE_FILE}"
    return
  fi
  grep -vx "${stage}" "${STATE_FILE}" >"${STATE_FILE}.tmp" 2>/dev/null || true
  mv "${STATE_FILE}.tmp" "${STATE_FILE}"
}

write_env_file() {
  local timestamp
  timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "DRY-RUN: would write ${ENV_FILE} from resolved configuration."
    return
  fi

  mkdir -p "$(dirname "${ENV_FILE}")"
  cat >"${ENV_FILE}" <<EOF
# Auto-generated by bootstrap_roman_photoz.sh
# Source pars: ${PARS_SOURCE}
# Generated at: ${timestamp}
LEPHAREDIR=${LEPHAREDIR}
LEPHAREWORK=${LEPHAREWORK}
INFORMER_MODEL_PATH=${INFORMER_MODEL_PATH}
EOF
}

download_aux_data() {
  if [[ "${FORCE_REFRESH}" != "true" ]] && stage_is_complete "aux_data"; then
    echo "==> LePhare auxiliary data already downloaded (per ${STATE_FILE}); skipping."
    return
  fi

  echo "==> Downloading LePhare auxiliary data..."
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "DRY-RUN: would run get_auxiliary_data() for LEPHAREDIR=${LEPHAREDIR}"
    return
  fi

  "${PYTHON_RUNNER_CMD[@]}" python - <<'PY'
import os

from lephare.data_retrieval import get_auxiliary_data
from roman_photoz.default_config_file import default_roman_config

get_auxiliary_data(
    lephare_dir=os.environ["LEPHAREDIR"],
    keymap=default_roman_config,
    additional_files=[
        "examples/COSMOS_MOD.list",
        # Ensure STAR SED payloads are fetched even if STAR_MOD_ALL.list
        # retrieval is temporarily unavailable during keymap expansion.
        "sed/STAR/PICKLES",
        "sed/STAR/WD",
        "sed/STAR/LAGET",
        "sed/STAR/BD",
    ],
)
print("Auxiliary data download complete.")
PY

  # Only mark the stage complete once get_auxiliary_data() has actually
  # returned successfully; if the download is interrupted partway through,
  # this line is never reached and the next run will correctly retry it
  # instead of assuming completion from partial files on disk.
  mark_stage_complete "aux_data"
}

build_model_if_needed() {
  CATALOG_PATH="${LEPHAREWORK}/${SIMULATED_CATALOG_FILENAME}"
  MODEL_PICKLE="${INFORMER_MODEL_PATH}/roman_model.pkl"
  INFORMER_RUN_DIR="$(dirname "${LEPHAREWORK}")/inform_roman"
  REBUILD_MODEL="false"

  if [[ "${BUILD_MODEL}" != "true" ]]; then
    echo "==> Skipping model build (BUILD_MODEL=false)."
    return
  fi

  if [[ "${FORCE_REFRESH}" == "true" || ! -f "${MODEL_PICKLE}" ]]; then
    REBUILD_MODEL="true"
  fi

  if [[ "${REBUILD_MODEL}" != "true" ]]; then
    echo "==> Model already exists at ${MODEL_PICKLE}; skipping rebuild."
    return
  fi

  echo "==> Preparing model rebuild..."
  if [[ -f "${MODEL_PICKLE}" ]]; then
    run_cmd rm -f "${MODEL_PICKLE}"
  fi
  if [[ -d "${INFORMER_RUN_DIR}" ]]; then
    run_cmd rm -rf "${INFORMER_RUN_DIR}"
  fi
  # Clear any prior completion marker up front: if this rebuild is
  # interrupted partway through, the state file must not claim the model
  # build finished.
  clear_stage "model_built"

  echo "==> Creating simulated catalog and Roman filter files..."
  CREATE_SIM_CMD=(
    "${PYTHON_RUNNER_CMD[@]}"
    roman-photoz-create-simulated-catalog
    --nobj "${NOBJ}"
    --output-path "${LEPHAREWORK}"
    --output-filename "${SIMULATED_CATALOG_FILENAME}"
  )
  if [[ "${FORCE_REFRESH}" == "true" ]]; then
    CREATE_SIM_CMD+=(--refresh-lib-mag)
  fi
  run_cmd "${CREATE_SIM_CMD[@]}"

  echo "==> Running informer + estimator stage..."
  run_cmd "${PYTHON_RUNNER_CMD[@]}" roman-photoz --input-filename "${CATALOG_PATH}"

  mark_stage_complete "model_built"
}

apply_cleanup() {
  CATALOG_PATH="${LEPHAREWORK}/${SIMULATED_CATALOG_FILENAME}"

  case "${CLEANUP_MODE}" in
  none)
    echo "==> Skipping cleanup (CLEANUP_MODE=none)."
    return
    ;;
  full | trimmed)
    echo "==> Removing intermediate files..."
    run_cmd rm -f "${CATALOG_PATH}" "${LEPHAREWORK}/roman_photoz.log"
    ;;
  *)
    echo "Unknown cleanup mode: ${CLEANUP_MODE}" >&2
    exit 1
    ;;
  esac

  if [[ "${CLEANUP_MODE}" == "trimmed" ]]; then
    echo "==> Trimming LEPHAREDIR (keeping opa/, ext/, vega/, alloutputkeys.txt)..."
    shopt -s nullglob
    for item in "${LEPHAREDIR}"/*; do
      name="$(basename "${item}")"
      case "${name}" in
      opa | ext | vega | alloutputkeys.txt)
        echo "    Keeping: ${name}"
        ;;
      *)
        run_cmd rm -rf "${item}"
        ;;
      esac
    done
    shopt -u nullglob
  else
    echo "==> Keeping full LEPHAREDIR contents (CLEANUP_MODE=full)."
  fi
}

verify_assets() {
  if [[ "${VERIFY_ASSETS}" != "true" ]]; then
    echo "==> Asset verification disabled."
    return
  fi

  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "DRY-RUN: would verify required bootstrap artifacts."
    return
  fi

  local missing=()
  for path in \
    "${LEPHAREDIR}/opa" \
    "${LEPHAREDIR}/ext" \
    "${LEPHAREDIR}/vega" \
    "${LEPHAREDIR}/alloutputkeys.txt"; do
    if [[ ! -e "${path}" ]]; then
      missing+=("${path}")
    fi
  done

  if [[ "${BUILD_MODEL}" == "true" ]]; then
    if [[ ! -f "${INFORMER_MODEL_PATH}/roman_model.pkl" ]]; then
      missing+=("${INFORMER_MODEL_PATH}/roman_model.pkl")
    fi
  fi

  if [[ ${#missing[@]} -gt 0 ]]; then
    echo "Bootstrap verification failed. Missing artifacts:" >&2
    printf '  - %s\n' "${missing[@]}" >&2
    exit 1
  fi

  echo "==> Asset verification succeeded."
}

PARS_FILE=""
CLI_OVERRIDES=()
DRY_RUN="false"
INITIAL_PYTHON_RUNNER="${PYTHON_RUNNER:-uv run}"

while [[ $# -gt 0 ]]; do
  case "$1" in
  --pars-file)
    PARS_FILE="$2"
    shift 2
    ;;
  --nobj)
    CLI_OVERRIDES+=("NOBJ=$2")
    shift 2
    ;;
  --simulated-catalog-filename)
    CLI_OVERRIDES+=("SIMULATED_CATALOG_FILENAME=$2")
    shift 2
    ;;
  --data-root)
    CLI_OVERRIDES+=("DATA_ROOT=$2")
    shift 2
    ;;
  --lepharedir)
    CLI_OVERRIDES+=("LEPHAREDIR=$2")
    shift 2
    ;;
  --lepharework)
    CLI_OVERRIDES+=("LEPHAREWORK=$2")
    shift 2
    ;;
  --informer-model-path)
    CLI_OVERRIDES+=("INFORMER_MODEL_PATH=$2")
    shift 2
    ;;
  --env-file)
    CLI_OVERRIDES+=("ENV_FILE=$2")
    shift 2
    ;;
  --cleanup-mode)
    CLI_OVERRIDES+=("CLEANUP_MODE=$2")
    shift 2
    ;;
  --build-model)
    CLI_OVERRIDES+=("BUILD_MODEL=true")
    shift
    ;;
  --force-refresh)
    CLI_OVERRIDES+=("FORCE_REFRESH=true")
    shift
    ;;
  --verify-assets)
    CLI_OVERRIDES+=("VERIFY_ASSETS=true")
    shift
    ;;
  --python-runner)
    CLI_OVERRIDES+=("PYTHON_RUNNER=$2")
    shift 2
    ;;
  --dry-run)
    DRY_RUN="true"
    shift
    ;;
  -h | --help)
    print_help
    exit 0
    ;;
  *)
    echo "Unknown option: $1" >&2
    print_help
    exit 1
    ;;
  esac
done

if [[ -z "${PARS_FILE}" && -f "${DEFAULT_PARS_FILE}" ]]; then
  PARS_FILE="${DEFAULT_PARS_FILE}"
fi

to_runner_array "${INITIAL_PYTHON_RUNNER}"
export PYTHONPATH="${SCRIPT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

RESOLVER_ARGS=(
  python
  -m
  roman_photoz.bootstrap_config
  --script-dir "${SCRIPT_DIR}"
  --format json
)
if [[ -n "${PARS_FILE}" ]]; then
  RESOLVER_ARGS+=(--pars-file "${PARS_FILE}")
fi
if [[ ${#CLI_OVERRIDES[@]} -gt 0 ]]; then
  for override in "${CLI_OVERRIDES[@]}"; do
    RESOLVER_ARGS+=(--override "${override}")
  done
fi

RESOLVER_OUTPUT="$("${PYTHON_RUNNER_CMD[@]}" "${RESOLVER_ARGS[@]}")"
# Importing roman_photoz (and transitively lephare) can print informational
# diagnostics to stdout before our resolver's own output. The resolver always
# prints its JSON payload as the final line, so take only that line rather
# than assuming the whole stdout stream is clean JSON.
RESOLVED_JSON="$(printf '%s\n' "${RESOLVER_OUTPUT}" | tail -n 1)"

# Convert the resolver's JSON output into shell-safe assignments (rather than
# parsing KEY=VALUE lines with IFS) so values can never be misinterpreted,
# even if they happen to contain '=' or other shell-significant characters.
CONFIG_ASSIGNMENTS="$(printf '%s' "${RESOLVED_JSON}" | "${PYTHON_RUNNER_CMD[@]}" python -c '
import json
import shlex
import sys

config = json.loads(sys.stdin.read())
for key, value in config.items():
    if isinstance(value, bool):
        value = "true" if value else "false"
    print(f"{key}={shlex.quote(str(value))}")
')"
eval "${CONFIG_ASSIGNMENTS}"

to_runner_array "${PYTHON_RUNNER}"

export LEPHAREDIR LEPHAREWORK INFORMER_MODEL_PATH
STATE_FILE="${LEPHAREWORK}/.bootstrap_state"

echo "==> Resolved bootstrap configuration"
echo "    Pars source:            ${PARS_SOURCE}"
echo "    Pars version:           ${PARS_VERSION}"
echo "    Data root:              ${DATA_ROOT}"
echo "    LEPHAREDIR:             ${LEPHAREDIR}"
echo "    LEPHAREWORK:            ${LEPHAREWORK}"
echo "    INFORMER_MODEL_PATH:    ${INFORMER_MODEL_PATH}"
echo "    .env file:              ${ENV_FILE}"
echo "    NOBJ:                   ${NOBJ}"
echo "    Simulated catalog:      ${SIMULATED_CATALOG_FILENAME}"
echo "    Build model:            ${BUILD_MODEL}"
echo "    Cleanup mode:           ${CLEANUP_MODE}"
echo "    Force refresh:          ${FORCE_REFRESH}"
echo "    Verify assets:          ${VERIFY_ASSETS}"
echo "    Python runner:          ${PYTHON_RUNNER}"
echo "    Dry run:                ${DRY_RUN}"

run_cmd mkdir -p "${LEPHAREDIR}" "${LEPHAREWORK}"
write_env_file
download_aux_data
build_model_if_needed
apply_cleanup
verify_assets

echo ""
echo "==> Bootstrap complete."
echo "    .env file:    ${ENV_FILE}"
echo "    Model:        ${INFORMER_MODEL_PATH}/roman_model.pkl"
echo "    LEPHAREDIR:   ${LEPHAREDIR}"
echo "    LEPHAREWORK:  ${LEPHAREWORK}"
echo ""
echo "To use in a new shell session:"
echo "    source ${ENV_FILE} && export LEPHAREDIR LEPHAREWORK INFORMER_MODEL_PATH"
