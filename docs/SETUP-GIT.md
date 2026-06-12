# Copy-paste Git setup for RamenAnime/Karakuri

Repository: **https://github.com/RamenAnime/Karakuri**

**If the repo does not exist yet:** sign in to GitHub, click **New repository**, name it `Karakuri`, leave it empty (no README), then run the blocks below.

Use these blocks in order on your Windows 11 work PC. Replace nothing except your email in block 1.

---

## Block 0: Create the repo on GitHub (one time)

1. Go to https://github.com/new
2. Owner: **RamenAnime**
3. Name: **Karakuri**
4. Description (paste this):

```text
Sovereign self-adapting floor robot: picks up dog toys into a box and cleans foam, hair, and trash. Immutable KODAMA core, RAIKO web research, SHIKAI vision, MUSUBI arm, HANE vacuum. Windows 11 + ROS 2.
```

5. Leave the repo **empty** (no README, no license, no gitignore)
6. Click **Create repository**

Optional topics: `robotics`, `ros2`, `computer-vision`, `python`, `autonomous`, `karakuri`

Full settings guide: [GITHUB-REPO-SETTINGS.md](GITHUB-REPO-SETTINGS.md)

---

## Block 1: Set your Git identity (once per PC)

```powershell
git config --global user.name "RamenAnime"
git config --global user.email "YOUR_GITHUB_EMAIL@example.com"
```

Use the same email as your GitHub account.

---

## Block 2: Clone the repo (first time)

```powershell
cd $HOME\Documents
git clone https://github.com/RamenAnime/Karakuri.git
cd Karakuri
```

---

## Block 3: Install the project

```powershell
.\scripts\install-windows.ps1
```

If the script is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\install-windows.ps1
```

Manual install if you prefer:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,research]"
copy .env.example .env
python -m karakuri doctor
```

---

## Block 4: Verify everything works

```powershell
.\.venv\Scripts\Activate.ps1
python -m karakuri doctor
python -m karakuri research query "ROS2 floor pick and place dog toy"
python -m karakuri research run --once
python -m karakuri promote --dry-run
python -m pytest -q
```

---

## Block 5: Open in Cursor

1. Open Cursor
2. **File > Open Folder**
3. Select `Documents\Karakuri`

---

## Block 6: Push your own changes (after you edit code)

```powershell
cd $HOME\Documents\Karakuri
git add -A
git commit -m "Describe your change"
git push origin main
```

---

## Block 7: First push (sole contributor, no co-authors)

The local repo is already one clean commit authored as **RamenAnime**. Push from your PC so GitHub links it to your account:

```powershell
cd $HOME\Documents\Karakuri
git config user.name "RamenAnime"
git config user.email "YOUR_GITHUB_EMAIL@example.com"
git remote add origin https://github.com/RamenAnime/Karakuri.git
git push -u origin main
```

Or use the helper script:

```powershell
.\scripts\first-push.ps1 -Email YOUR_GITHUB_EMAIL@example.com
```

**Do not** add `Co-authored-by:` lines to commit messages. Only push from your account.

If the remote already has wrong history:

```powershell
git push -u origin main --force
```

Only use `--force` on a new empty repo you own.

---

## Block 8: Emergency stop

```powershell
python -m karakuri stop
python -m karakuri stop --clear
```

---

## Ubuntu / WSL2 (for ROS 2 later)

```bash
cd ~/Karakuri
bash scripts/install-wsl.sh
source .venv/bin/activate
python -m karakuri doctor
```

See [WINDOWS.md](WINDOWS.md) for WSL2 install steps on Windows 11.
