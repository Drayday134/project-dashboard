# Project Dashboard

Flask web app for viewing all Workhorse2025 projects. Simple read-only dashboard.

## Quick Reference

- **Run**: `source venv/bin/activate && python app.py`
- **URL**: http://localhost:5000
- **Login**: dragon / dragon123 (or set DASHBOARD_USER / DASHBOARD_PASS env vars)
- **Secret key**: set DASHBOARD_SECRET_KEY in production

## Architecture

Single file: `app.py`. Flask with Jinja2 templates.

```
app.py              # Routes, auth, file browsing API
templates/          # HTML (dashboard.html, login.html, browse.html)
static/             # CSS/JS
```

## Endpoints

- `/` - Main dashboard (lists projects)
- `/browse/<path>` - File browser
- `/api/projects` - JSON project list
- `/api/browse/<path>` - JSON directory listing
- `/api/file/<path>` - Read file contents (max 1MB, text only)

## Projects It Tracks

Hardcoded in `get_projects()`: threat-intel-aggregator, trading, fishtracker, sectop, claude-git-control, claude-backups, project-dashboard.

## Security

- Path traversal protection (checks realpath stays under PROJECT_ROOT)
- Session-based auth
- Skips .dot dirs, node_modules, __pycache__, venv in browsing
