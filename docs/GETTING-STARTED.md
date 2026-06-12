# Getting started

Repository: **https://github.com/RamenAnime/Karakuri**

Local folder (Jason's PC):

```text
C:\Users\Jason Jones\Downloads\Karakuri
```

---

## Git Bash: daily commands

```bash
cd "/c/Users/Jason Jones/Downloads/Karakuri"
git status
git add -A
git commit -m "Describe your change"
git push origin main
```

Set identity once (use your GitHub email):

```bash
git config user.name "RamenAnime"
git config user.email "your-github-email@example.com"
```

Do not add `Co-authored-by:` lines to commits.

---

## Install Python package

Requires Python 3.10+ and Git.

```bash
cd "/c/Users/Jason Jones/Downloads/Karakuri"
python -m venv .venv
source .venv/Scripts/activate
pip install -e ".[dev,research]"
cp .env.example .env
python -m karakuri doctor
python -m pytest -q
```

Windows CMD equivalent for venv activate:

```cmd
.venv\Scripts\activate.bat
```

---

## GitHub repo description

Paste in repo settings on github.com:

```text
Sovereign self-adapting floor robot: picks up dog toys into a box and cleans foam, hair, and trash. Immutable KODAMA core, RAIKO web research, SHIKAI vision, MUSUBI arm, HANE vacuum. Windows 11 + ROS 2.
```

Suggested topics: `robotics`, `ros2`, `computer-vision`, `python`, `autonomous`, `karakuri`

---

## Emergency stop

```bash
python -m karakuri stop
python -m karakuri stop --clear
```

---

## Related docs

| Doc | Topic |
|-----|--------|
| [README.md](../README.md) | Full project plan |
| [FUSION.md](FUSION.md) | All codenames |
| [ROADMAP.md](ROADMAP.md) | Build phases 0 to 8 |
| [HARDWARE-BLUEPRINT.md](HARDWARE-BLUEPRINT.md) | Robot BOM and layout |
| [GITHUB.md](GITHUB.md) | Sole contributor rules |
| [WINDOWS.md](WINDOWS.md) | Windows 11 details |
| [../Downloads-Setup/GIT-BASH.txt](../Downloads-Setup/GIT-BASH.txt) | Copy-paste Git blocks |
