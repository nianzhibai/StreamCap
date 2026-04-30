#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/venv"
VENV_ACTIVATE="${VENV_DIR}/bin/activate"
VENV_PYTHON="${VENV_DIR}/bin/python3"
ENV_FILE="${PROJECT_DIR}/.env"
ENV_EXAMPLE_FILE="${PROJECT_DIR}/.env.example"
REQUIREMENTS_FILE="${PROJECT_DIR}/requirements.txt"
REQUIREMENTS_WEB_FILE="${PROJECT_DIR}/requirements-web.txt"
REQUIREMENTS_HASH_FILE="${VENV_DIR}/.requirements.txt.sha256"
REQUIREMENTS_WEB_HASH_FILE="${VENV_DIR}/.requirements-web.txt.sha256"

APT_UPDATED=0

log() {
  printf '[StreamCap] %s\n' "$1"
}

have_command() {
  command -v "$1" >/dev/null 2>&1
}

run_apt() {
  if [ "$(id -u)" -eq 0 ]; then
    apt-get "$@"
  else
    sudo apt-get "$@"
  fi
}

apt_update_once() {
  if [ "${APT_UPDATED}" -eq 0 ]; then
    log "Updating apt package index..."
    run_apt update
    APT_UPDATED=1
  fi
}

install_package_if_missing() {
  local package_name="$1"
  local check_command="$2"

  if have_command "${check_command}"; then
    return 0
  fi

  apt_update_once
  log "Installing missing package: ${package_name}"
  run_apt install -y "${package_name}"
}

ensure_python_venv() {
  if python3 -m venv --help >/dev/null 2>&1; then
    return 0
  fi

  apt_update_once
  log "Installing missing package: python3-venv"
  run_apt install -y python3-venv
}

bootstrap_env_file() {
  if [ -f "${ENV_FILE}" ]; then
    return 0
  fi

  log "Creating .env from .env.example"
  cp "${ENV_EXAMPLE_FILE}" "${ENV_FILE}"
  log ".env created. Edit ${ENV_FILE} if you need to change PLATFORM, HOST, PORT, or web login options."
}

venv_is_ready() {
  [ -f "${VENV_ACTIVATE}" ] && [ -x "${VENV_PYTHON}" ]
}

create_virtualenv() {
  if venv_is_ready; then
    return 0
  fi

  if [ -d "${VENV_DIR}" ]; then
    log "Rebuilding incomplete virtual environment in ${VENV_DIR}"
    python3 -m venv --clear "${VENV_DIR}"
    return 0
  fi

  log "Creating virtual environment in ${VENV_DIR}"
  python3 -m venv "${VENV_DIR}"
}

file_sha256() {
  if have_command sha256sum; then
    sha256sum "$1" | awk '{print $1}'
    return 0
  fi

  if have_command shasum; then
    shasum -a 256 "$1" | awk '{print $1}'
    return 0
  fi

  python3 -c 'import hashlib, pathlib, sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$1"
}

requirement_hash_matches() {
  local requirement_file="$1"
  local hash_file="$2"
  local current_hash

  if [ ! -f "${hash_file}" ]; then
    return 1
  fi

  current_hash="$(file_sha256 "${requirement_file}")"
  [ "$(cat "${hash_file}")" = "${current_hash}" ]
}

write_requirement_hash() {
  local requirement_file="$1"
  local hash_file="$2"

  file_sha256 "${requirement_file}" > "${hash_file}"
}

install_requirement_if_needed() {
  local requirement_file="$1"
  local hash_file="$2"
  local force_install="${3:-0}"
  local requirement_name

  requirement_name="$(basename "${requirement_file}")"

  if [ "${force_install}" -eq 0 ] && requirement_hash_matches "${requirement_file}" "${hash_file}"; then
    log "Python dependencies already match ${requirement_name}; skipping"
    return 0
  fi

  log "Installing Python dependencies from ${requirement_name}"
  python3 -m pip install -r "${requirement_file}"
  write_requirement_hash "${requirement_file}" "${hash_file}"
}

install_python_dependencies() {
  # shellcheck disable=SC1091
  source "${VENV_ACTIVATE}"

  local force_install=0

  if ! python3 -m pip check >/dev/null 2>&1; then
    log "Installed Python packages are incomplete or inconsistent; reinstalling requirements"
    force_install=1
  fi

  install_requirement_if_needed "${REQUIREMENTS_FILE}" "${REQUIREMENTS_HASH_FILE}" "${force_install}"
  install_requirement_if_needed "${REQUIREMENTS_WEB_FILE}" "${REQUIREMENTS_WEB_HASH_FILE}" "${force_install}"
}

start_application() {
  # shellcheck disable=SC1091
  source "${VENV_ACTIVATE}"

  log "Starting StreamCap with .env configuration"
  cd "${PROJECT_DIR}"
  exec python3 main.py
}

main() {
  if ! have_command python3; then
    apt_update_once
    log "Installing missing package: python3"
    run_apt install -y python3
  fi

  install_package_if_missing ffmpeg ffmpeg
  ensure_python_venv
  bootstrap_env_file
  create_virtualenv
  install_python_dependencies
  start_application
}

main "$@"
