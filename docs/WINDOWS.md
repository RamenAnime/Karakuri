# Windows 11 onboarding (work PC)

Use this guide to set up KARAKURI on a Windows 11 machine for development. ROS 2 work stays on WSL2 later; the Windows side runs the Python core, watchdog, and research stubs.

---

## 1. Install Git

Install [Git for Windows](https://git-scm.com/download/win) or use winget:

```powershell
winget install --id Git.Git -e
```

Close and reopen PowerShell, then confirm:

```powershell
git --version
```

Set your identity (use your work email if this is a work PC):

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

See [docs/GITHUB.md](GITHUB.md) for creating the remote repo and keeping yourself as the sole contributor.

---

## 2. Install Python 3.11+

KARAKURI requires Python 3.10 or newer; use 3.11 or 3.12 on Windows.

**Option A - winget (recommended):**

```powershell
winget install --id Python.Python.3.12 -e
```

**Option B - installer:**

Download Python 3.11+ from [python.org](https://www.python.org/downloads/windows/). During setup, check **Add python.exe to PATH**.

Confirm in a new PowerShell window:

```powershell
python --version
```

You should see `Python 3.11.x` or newer.

---

## 3. Clone the repo

Pick a folder for projects, then clone:

```powershell
cd $HOME\Projects
git clone https://github.com/YOUR_USER/karakuri.git
cd karakuri
```

If you use SSH:

```powershell
git clone git@github.com:YOUR_USER/karakuri.git
cd karakuri
```

---

## 4. Run the Windows installer (optional shortcut)

From the repo root in PowerShell:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\scripts\install-windows.ps1
```

The script checks Git and Python, creates a virtual environment, installs dev dependencies, copies `.env.example` to `.env` if needed, and runs `karakuri doctor`.

---

## 5. Manual setup (same result as the script)

If you prefer to run steps yourself:

```powershell
cd $HOME\Projects\karakuri

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e ".[dev]"

copy .env.example .env
```

---

## 6. Verify the install

With the venv activated:

```powershell
python -m karakuri doctor
```

Expected output includes project root, STOP flag status, core integrity OK, and allowlist counts.

Test the emergency stop:

```powershell
python -m karakuri stop
python -m karakuri doctor
python -m karakuri stop --clear
```

Or use the console entry point after install:

```powershell
karakuri doctor
karakuri stop
karakuri stop --clear
```

---

## 7. Optional: WSL2 for future ROS 2

ROS 2 Humble/Jazzy targets Linux. On Windows, use WSL2 with Ubuntu for simulation and robot packages later. You can develop the Python core on Windows now and add WSL when you reach Phase 2.

**Enable WSL2 (admin PowerShell):**

```powershell
wsl --install -d Ubuntu
```

Reboot if prompted, create your Linux user, then inside Ubuntu:

```bash
cd /mnt/c/Users/YOUR_USER/Projects/karakuri
bash scripts/install-wsl.sh
```

That script installs Python tooling on the Ubuntu side and prepares the same venv workflow. Keep one canonical clone (Windows path or WSL home) to avoid drift.

---

## 8. Daily workflow

```powershell
cd $HOME\Projects\karakuri
.\.venv\Scripts\Activate.ps1

karakuri doctor
karakuri run --once
```

Run tests:

```powershell
pytest
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `python` not found | Reinstall Python with **Add to PATH**, or use `py -3.12` instead of `python` |
| `Activate.ps1` blocked | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `pip install -e ".[dev]"` fails | Upgrade pip: `python -m pip install --upgrade pip setuptools wheel` |
| Core integrity FAIL | Do not edit files under `core/` by hand; restore from git or re-clone |
| Doctor exits 1 with STOP engaged | Run `karakuri stop --clear` |

---

## Related docs

- [GITHUB.md](GITHUB.md) - create repo, push, sole contributor hygiene
- [ARCHITECTURE.md](ARCHITECTURE.md) - rings of trust and kill switch
- [ROBOT-MISSION.md](ROBOT-MISSION.md) - floor robot goals
