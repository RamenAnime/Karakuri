# GitHub: RamenAnime/Karakuri

Repository: **https://github.com/RamenAnime/Karakuri**

Local folder:

```text
C:\Users\Jason Jones\Downloads\Karakuri
```

Setup guide: [GETTING-STARTED.md](GETTING-STARTED.md)

---

## Repo description (paste in GitHub settings)

```text
Sovereign self-adapting floor robot: picks up dog toys into a box and cleans foam, hair, and trash. Immutable KODAMA core, RAIKO web research, SHIKAI vision, MUSUBI arm, HANE vacuum. Windows 11 + ROS 2.
```

Topics: `robotics`, `ros2`, `computer-vision`, `python`, `autonomous`, `karakuri`

---

## Git Bash: first push

```bash
cd "/c/Users/Jason Jones/Downloads/Karakuri"
git config user.name "RamenAnime"
git config user.email "your-github-email@example.com"
git add -A
git commit -m "Initial KARAKURI fusion stack"
git remote remove origin 2>/dev/null
git remote add origin https://github.com/RamenAnime/Karakuri.git
git branch -M main
git push -u origin main
```

---

## Sole contributor rules

1. Commit and push only from your PC with your GitHub email configured.
2. Do not add `Co-authored-by:` lines to commit messages.
3. Do not merge bot-authored PRs into `main` if you want a single face on the Contributors graph.
4. Check **Insights > Contributors** after push. Only **RamenAnime** should appear.

### Fix wrong authors on `main`

```bash
git checkout --orphan clean-main
git add -A
git commit -m "Initial KARAKURI fusion stack"
git branch -M main
git push -f origin main
```

Use force push only on repos you own and others have not cloned yet.

---

## Daily workflow

```bash
cd "/c/Users/Jason Jones/Downloads/Karakuri"
git status
git add -A
git commit -m "Describe your change"
git push origin main
```

---

## Related

- [GETTING-STARTED.md](GETTING-STARTED.md)
- [WINDOWS.md](WINDOWS.md)
- [README.md](../README.md)
