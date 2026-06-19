# Database Migrations

This folder keeps reviewable SQL artifacts for the KARAKURI local database.

`001_hardened_schema.sql` mirrors the audited schema definitions in
`karakuri/database/spec.py` and the SQLite renderer in
`karakuri/database/sqlite.py`.

Refresh the migration after schema edits:

```powershell
python -m karakuri database schema --output database/migrations/001_hardened_schema.sql
```
