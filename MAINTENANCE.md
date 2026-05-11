# Maintenance

## Day-to-day

Most things are automated via Airflow. The DAGs run on schedule:

| DAG | What it does | Schedule |
|-----|--------------|----------|
| `dag_bdxc` | Scrapes concerts from bdxc.fr → Postgres | Check Airflow UI |
| `dag_ecrantotal` | Scrapes films from ecran-total.fr → Postgres, fetches genres from Wikipedia | Check Airflow UI |

Monitor failures: Airflow sends a Discord alert to `URL_WEBHOOK_DIDI` on task failure.

---

## Local dev commands

```bash
# Start everything
docker compose up -d

# Rebuild after code changes
docker compose up -d --build

# Stop
docker compose down

# Nuke volumes (resets all DB data — careful)
docker compose down -v
```

---

## Code quality

Run before every commit (pre-commit does this automatically on `git commit`):

```bash
poetry run pre-commit run --all-files
```

Hooks: black (formatter), flake8 (linter), mypy (type checker).

To reinstall hooks after a fresh clone or venv recreation:
```bash
poetry run pre-commit install
```

---

## Tests

```bash
# Fast — no network, run anytime
poetry run pytest tests/ -m "not integration" -v

# Slow — hits Wikipedia API, run when changing genre extraction
poetry run pytest tests/ -m integration -v
```

Run integration tests after any change to `fetch_wikipedia_genres`, `_extract_genres`, or `_GENRE_KEYWORDS` in `scrapers/ecrantotal_pipeline.py`.

---

## Adding a new scraper

1. Create `scrapers/your_pipeline.py` — use `pg_connection()` from `utils/db.py` for Postgres
2. Create `dags/dag_your_pipeline.py` — wire up the task + `send_discord_alert` on failure
3. Add the DAG to `docker-compose.yml` volume mounts if needed

---

## Secret rotation

If a secret leaks (webhook URL, API token, DB password), regenerate it at the source and update `.env`. Secrets in use:

| Variable | Where to regenerate |
|----------|-------------------|
| `URL_WEBHOOK_DIDI` | Discord → Server Settings → Integrations → Webhooks |
| `CLOUDFLARE_TUNNEL_TOKEN` | Cloudflare Zero Trust → Networks → Tunnels → your tunnel → Configure |
| `POSTGRES_PASSWORD` | Change in `.env`, then `docker compose down -v && docker compose up -d` |
| `AIRFLOW_SECRET_KEY` | Generate a new random string, update `.env`, restart Airflow |

If a secret ends up in git history:
```bash
# Commit all work FIRST before running this
git add -A && git commit -m "wip: save before history rewrite"

pipx install git-filter-repo  # one-time install
git filter-repo --invert-paths --path .env_backup --force
# re-add remote if needed: git remote add origin <url>
# force-push: git push --force
```

---

## Dependency updates

```bash
# Update all deps to latest compatible versions
poetry update

# Add a new dep
poetry add package-name

# Add a dev-only dep
poetry add --group dev package-name
```

---

## Fresh clone setup

```bash
git clone <repo>
cd echoculture
cp .env.example .env   # fill in real values
poetry install
poetry run pre-commit install
docker compose up -d --build
```
