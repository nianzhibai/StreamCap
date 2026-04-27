# Debian Start Script Design

## Goal

Add a Debian-oriented startup script that prepares the local machine and launches StreamCap using the `.env` configuration.

## Scope

- Check required local dependencies for Debian runtime.
- Install missing system packages when possible.
- Create or reuse the local virtual environment.
- Install Python dependencies from the repository requirements files.
- Create `.env` from `.env.example` if it does not exist.
- Start the app with `python3 main.py`, letting runtime behavior come from `.env`.

## Design

### Script behavior

- Add `start_debian.sh` in the repository root.
- The script runs with `bash` and exits on errors.
- Required system tools:
  - `python3`
  - `python3-venv`
  - `ffmpeg`
- When tools are missing, use `apt-get` to install the corresponding Debian packages.
- If the current user is not root, use `sudo` for package installation.

### Python environment

- Create `venv/` when missing.
- Upgrade `pip` inside the virtual environment.
- Install both `requirements.txt` and `requirements-web.txt`.

### Environment file

- If `.env` is missing, copy `.env.example` to `.env`.
- Do not rewrite existing `.env`.
- Do not override user values; startup behavior must be determined by the file contents.

### Launch

- Activate the virtual environment.
- Run `python3 main.py`.

## Notes

- The script is intentionally generic and does not force web mode.
- Users can change `PLATFORM`, `HOST`, `PORT`, and other options by editing `.env`.
