#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/venv"
ENV_FILE="${PROJECT_DIR}/.env"
ENV_EXAMPLE_FILE="${PROJECT_DIR}/.env.example"

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
  log ".env created. Edit ${ENV_FILE} if you need to change PLATFORM, HOST, PORT, or other options."
}

create_virtualenv() {
  if [ -d "${VENV_DIR}" ]; then
    return 0
  fi

  log "Creating virtual environment in ${VENV_DIR}"
  python3 -m venv "${VENV_DIR}"
}

install_python_dependencies() {
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"

  log "Upgrading pip"
  python3 -m pip install --upgrade pip

  log "Installing Python dependencies"
  python3 -m pip install -r "${PROJECT_DIR}/requirements.txt"
  python3 -m pip install -r "${PROJECT_DIR}/requirements-web.txt"
}

start_application() {
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"

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
