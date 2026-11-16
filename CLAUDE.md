# AR Cooling Solutions website

Business website for AR Cooling Solutions, Hyderabad (AC & HVAC products, services, spare
parts). Live at https://arcooling.in. The owner is not a developer: explain things in plain
words, and ask before anything that changes the live site.

## How it is built

- **Flask app** (`app.py`) with Jinja templates (`templates/`), CSS/JS in `static/`.
- **Content** (products, services, spare parts, compressor models, home page items) is in a
  SQLite database (`store.py`), first filled from the JSON files in `data/`. On the live
  server the admin edits the database; `data/` in git is the starting copy.
- **Social posts** stay in `data/social/posts.json` (pictures by `tools/make_social_posts.py`);
  each has a share page at `/go/<id>/` (`render_share_page` in `app.py`).
- **Enquiries** go from the visitor's browser to FormSubmit, which emails them; the server
  stores nothing about visitors.
- **Admin** at `/admin` (login from env vars `AR_ADMIN_USERNAME` / `AR_ADMIN_PASSWORD`).

## Where it runs

- **Live:** an Oracle Cloud Always Free server (E2.1.Micro, 1 GB RAM + 2 GB swap, Ubuntu
  24.04), IP 140.245.253.10. Caddy (HTTPS) → Waitress (`serve.py`) → Flask. Setup and
  operations: `deploy/oracle/README.md`. The server pulls `main` from GitHub every 5 minutes
  and restarts itself (`deploy/oracle/update.sh`), so **merging to `main` = going live**.
- **GitHub Pages** still builds a static copy on every push to `main`
  (`tools/build_static.py`); it is no longer what visitors see, but the build must pass.
- SSH (read-only checks only unless asked): `ssh -i ~/.ssh/ar-cooling.key ubuntu@140.245.253.10`.

## Commands (Windows; use the project venv)

```
.venv/Scripts/python app.py                 # dev server with reload, http://127.0.0.1:5000
.venv/Scripts/python serve.py               # production-style server, http://127.0.0.1:8080
.venv/Scripts/python tools/check_site.py    # full automated check (run before any PR)
.venv/Scripts/python tools/check_site.py --live   # also check https://arcooling.in
.venv/Scripts/python tools/build_static.py  # static build + internal link check
```

## Rules for every change

- Work on a branch (`feature/...` or `fix/...`), never directly on `main`; the owner merges PRs.
- Stage files by name. The owner may have unrelated uncommitted edits (e.g. in `data/`);
  never sweep them into a commit.
- Never commit, print or change secrets: `.env`, `/etc/ar-cooling.env`, SSH keys.
- Keep the 1 GB server in mind: no heavy dependencies or background workers without a reason.
- Public pages keep one URL each (trailing slash); search ranking and existing social links
  depend on current URLs, including `/go/<id>/`.
- Match the existing code style: small functions, comments that say *why*, plain-English UI text.
- Commit messages end with: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## The website team

Six agents in `.claude/agents/` (requirements-analyst, architect, developer, tester, reviewer,
deployer) work through `/website-team <request>`. They hand work to each other through
`docs/work/<date>-<slug>/` (01-requirements … 06-deployment).
