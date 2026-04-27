# Debian Start Script Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Debian startup script that auto-prepares dependencies, initializes `.env`, and launches the project using `python3 main.py`.

**Architecture:** Use a single root-level shell script for setup and launch, keeping all runtime configuration in `.env`. Add a small repository test that locks the expected script structure and update README usage instructions.

**Tech Stack:** Bash, Debian `apt-get`, Python virtual environments, `unittest`

---

### Task 1: Lock Script Requirements

**Files:**
- Create: `tests/test_start_debian_script.py`
- Create: `start_debian.sh`

- [ ] Step 1: Add a failing test that requires the script to exist and include dependency checks, `.env` bootstrap, and `python3 main.py`.
- [ ] Step 2: Run `venv/bin/python -m unittest tests.test_start_debian_script -v` and confirm it fails before the script exists.
- [ ] Step 3: Implement the script minimally to satisfy those requirements.
- [ ] Step 4: Re-run `venv/bin/python -m unittest tests.test_start_debian_script -v` and confirm it passes.

### Task 2: Document Usage

**Files:**
- Modify: `README.md`

- [ ] Step 1: Add a Debian startup section that tells users to run `bash start_debian.sh`.
- [ ] Step 2: Explain that runtime options are read from `.env`.

### Task 3: Verify Final State

**Files:**
- Verify only

- [ ] Step 1: Run `venv/bin/python -m unittest tests.test_start_debian_script -v`.
- [ ] Step 2: Run `bash -n start_debian.sh`.
- [ ] Step 3: Review the script to confirm it does not overwrite an existing `.env` or force web mode.
