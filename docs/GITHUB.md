# GitHub setup for RamenAnime/Karakuri

Repository: **https://github.com/RamenAnime/Karakuri**

Copy-paste blocks: [SETUP-GIT.md](SETUP-GIT.md)

Use this when you create or sync the GitHub repository from your work PC. The goal is a clean history where **you** are the only contributor on GitHub.

---

## 1. Create an empty repository on GitHub

1. Sign in to [GitHub](https://github.com).
2. Click **New repository**.
3. Name it `Karakuri` under account `RamenAnime`.
4. Choose **Private** or **Public**.
5. Do **not** initialize with a README, `.gitignore`, or license if you already have a local repo with those files.
6. Click **Create repository**.

GitHub shows push instructions for an empty repo. Keep that page open.

---

## 2. Configure Git on your machine

Run once on the PC that will own the history (Windows PowerShell or WSL):

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Use the same email as your GitHub account if you want verified commits on github.com.

Check:

```powershell
git config --global user.name
git config --global user.email
```

---

## 3. Push your local repo

From your KARAKURI clone:

```powershell
cd $HOME\Projects\karakuri
git remote add origin https://github.com/RamenAnime/Karakuri.git
git branch -M main
git push -u origin main
```

SSH equivalent:

```powershell
git remote add origin git@github.com:RamenAnime/Karakuri.git
git push -u origin main
```

If `origin` already exists, update it:

```powershell
git remote set-url origin https://github.com/RamenAnime/Karakuri.git
git push -u origin main
```

---

## 4. Stay the sole contributor

GitHub lists everyone who authored commits that reached the default branch. To keep the contributors list to yourself:

### Push only from your machine

- Commit and push from the work PC where you set `user.name` and `user.email`.
- Avoid merging PRs authored by bots or other accounts into `main`.
- Do not use GitHub web editor or Copilot commit flows on `main` if they attach a different identity.

### Avoid co-authored commits

Do not add lines like this in commit messages:

```text
Co-authored-by: Some Bot <bot@users.noreply.github.com>
```

If you use an AI assistant locally, squash or amend before push so the final commit on `main` has only your author line.

### Squash messy history before the first push

If your local log has unwanted authors or experimental commits:

```powershell
git checkout main
git reset --soft HEAD~N
git commit -m "Initial KARAKURI scaffold"
git push -u origin main
```

Replace `N` with the number of commits to fold into one. Only do this before others clone the repo.

### Rewrite history on a fresh remote (last resort)

If you already pushed and need a single-author history:

```powershell
git checkout --orphan clean-main
git add -A
git commit -m "Initial KARAKURI scaffold"
git branch -M main
git push -f origin main
```

Force push only when you are sure no one else depends on the old history.

---

## 5. Verify on GitHub

After push:

1. Open the repo on GitHub.
2. Check **Insights** > **Contributors** (or the contributor avatars on the main page).
3. Confirm only your account appears.

If a second contributor shows up, inspect recent commits (`git log --format=fuller`) for wrong `Author` or `Co-authored-by` trailers, then fix with squash or amend and force-push as above.

---

## 6. Ongoing workflow

```powershell
git status
git add -A
git commit -m "Describe your change"
git push
```

Use branches for experiments; merge to `main` with squash if you want one commit per feature and a single author on each squash commit (the merger's identity).

---

## Related

- [WINDOWS.md](WINDOWS.md) - clone and install on Windows 11
- [README.md](../README.md) - project overview
