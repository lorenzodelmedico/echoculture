# EchoCulture — Architecture

## Full data flow — Medallion architecture

MongoDB and DBT serve different layers of the pipeline. The complete flow is:

```
[BDXC API / Écran Total HTML]
        │
        ▼
MongoDB — echoculture_bronze
  ├── bdxc_events_raw         (full raw JSON payload per run — replayable archive)
  ├── bdxc_sync_history       (hash of last payload — deduplication gate)
  └── ecrantotal_sync_history (hash of last HTML — deduplication gate)
        │
        │  Scrapers transform & upsert
        ▼
PostgreSQL — public schema    (Silver: structured, typed)
  ├── events
  ├── movies
  └── event_prices
        │
        │  DBT transforms
        ▼
PostgreSQL — public schema    (Gold: clean, tested, business-ready)
  ├── stg_events    (view)
  ├── stg_movies    (view)
  ├── int_events    (view)
  ├── int_movies    (view)
  ├── fct_concerts  (table ← read by the UI)
  └── fct_films     (table ← read by the UI)

Spark job runs between scrape and dbt_run in dag_ecrantotal:
  reads movies WHERE genres IS NULL → 4 parallel Wikipedia workers → writes back
```

| Layer | Store | Managed by |
|-------|-------|-----------|
| Bronze | MongoDB | Scrapers (raw dump + hash log) |
| Silver | PostgreSQL raw tables | Scrapers (upsert with signature dedup) |
| Gold | PostgreSQL stg_\* / int_\* / fct_\* | DBT |

---

## MongoDB — why it's still needed, why DBT can't touch it

MongoDB is **not** replaced by DBT. It serves two things DBT cannot:

**A — Raw archive (bronze layer)**
`bdxc_events_raw` stores the full unmodified BDXC API response as a JSON document on
every new payload. If a scraper bug corrupts PostgreSQL data, you can replay from Mongo
without re-hitting the API. This is the "you can never re-fetch the past" insurance
policy.

**B — Change detection / idempotency**
Both pipelines hash their payload and compare it against the last stored hash in Mongo
(`bdxc_sync_history`, `ecrantotal_sync_history`). If the hash matches → skip the run.
This prevents redundant upserts on unchanged source data without needing a
`last_modified` column on an API we don't control.

**Why DBT doesn't touch MongoDB:**
DBT is SQL-only by design. It connects to a relational warehouse (Postgres, Snowflake,
BigQuery…) and compiles Jinja + SQL into queries. There is no MongoDB adapter. DBT picks
up the data *after* scrapers have landed it in PostgreSQL — MongoDB is upstream of DBT's
scope.

---

## What DBT brings

- **Transform isolation** — scrapers own extraction, DBT owns transformation. A broken
  transform never corrupts `events` or `movies`. Rolling back is `dbt run` from a
  known-good commit.
- **Data quality gates** — `not_null`, `unique`, `assert_min_price_lte_max_price` run
  after every scrape. If they fail, Airflow marks the DAG red *before* the mart is
  rebuilt. Bad data never reaches the UI.
- **Reproducibility** — drop `fct_concerts`, run `dbt run --select fct_concerts+`, it's
  back.
- **Lineage** — `dbt docs generate` builds a DAG graph showing which tables feed which.
- **DE portfolio signal** — staging → intermediate → marts is the standard
  Medallion/layered architecture recognised immediately by any data engineer.

---

## What Spark brings

The one workload in this project that is embarrassingly parallel: Wikipedia API calls.
Each call is independent (one movie = one HTTP request + one DB write). Sequential calls
at 1.5 s/movie for ~200 movies ≈ 5 minutes. With 4 workers each sleeping independently:
effective throughput ≈ 4× without exceeding Wikimedia's 50 req/s limit.

**Today** — `local[4]`: 4 threads inside the Airflow container (Java 17 is already
there; no separate cluster needed).

**Tomorrow** — to go distributed, change one line in `wikipedia_genre_enrichment.py`:
```python
.master("spark://echoculture_spark:7077")   # point at the spark container
```
The job code is identical. That's the point of writing it as a proper Spark job.

**Portfolio signal** — even in local mode this demonstrates: knowing when to reach for
distributed compute, structuring a `mapPartitions` job correctly (per-partition DB
connections, independent rate limiting), and keeping the driver thin.

---

## How to use it

### Airflow DAGs (automated)

| DAG | Schedule | Chain |
|-----|----------|-------|
| `dag_bdxc` | `@daily` | scrape → `dbt run fct_concerts+` → `dbt test stg_events` |
| `dag_ecrantotal` | `@weekly` | scrape → Spark Wikipedia enrich → `dbt run fct_films+` → `dbt test stg_movies` |

### DBT commands (manual — run inside the Airflow container)

```bash
# Prefix for all commands:
docker exec echoculture-airflow-webserver-1 \
  dbt <command> --profiles-dir /opt/airflow/dbt --project-dir /opt/airflow/dbt
```

| Command | What it does |
|---------|-------------|
| `dbt debug` | Tests the Postgres connection. "Connection OK" = ready. Git warning is harmless — we have no dbt packages. |
| `dbt seed` | Loads `seeds/genre_family_map.csv` into Postgres. Re-run after editing the CSV. |
| `dbt run` | Rebuilds all 6 models in dependency order. Views are replaced in-place; tables are dropped and recreated. |
| `dbt run --select fct_concerts+` | Rebuilds `fct_concerts` **and all its upstream dependencies** (`int_events` → `stg_events`). |
| `dbt run --select stg_movies` | Rebuilds only `stg_movies` (no upstream, no downstream). |
| `dbt test` | Runs all 9 tests: 8 schema tests (not_null/unique from `.yml` files) + 1 singular test. Non-zero exit = Airflow marks task failed. |
| `dbt test --select stg_events` | Runs only the 4 tests defined on `stg_events`. |
| `dbt docs generate` | Writes documentation JSON to `dbt/target/`. |
| `dbt docs serve --port 8083` | Starts a lineage + column docs UI on port 8083 (avoids conflict with Airflow on 8080). |

**The `+` suffix explained** — `fct_concerts+` means "this model AND all its ancestors".
Without `+`, dbt builds `fct_concerts` in isolation, which may read from stale upstream
views. With `+`, dbt resolves the full dependency chain and runs models in order.

### Spark (manual)

```bash
# Run the enrichment job (Airflow container has Java 17 — no cluster needed):
docker exec echoculture-airflow-webserver-1 \
  python /opt/airflow/spark/jobs/wikipedia_genre_enrichment.py

# Spark master UI (when the spark container is running):
open http://localhost:8085

# Force re-enrichment (clears genres so the job picks them up again):
docker exec echoculture_pg psql -U lorenzo -d echoculture \
  -c "UPDATE movies SET genres = NULL;"
# then re-run the job
```

The job is idempotent — it queries `WHERE genres IS NULL`, so re-running it on an
already-enriched database is a no-op.

---

## Critical files

### DBT configuration

| File | Role |
|------|------|
| `dbt/dbt_project.yml` | Project name, directory layout, materialization rules: staging/intermediate = **view** (no storage cost, always fresh), marts = **table** (pre-computed for fast UI reads) |
| `dbt/profiles.yml` | Postgres connection. Reads `POSTGRES_USER/PASSWORD/DB` from `.env` (already injected by Docker). Host defaults to `db_postgres` (Docker service name). |

### Sources

| File | Role |
|------|------|
| `dbt/models/sources.yml` | Registers the three raw tables written by scrapers (`events`, `movies`, `event_prices`) so DBT can track lineage across the silver boundary. Referenced in SQL as `{{ source('echoculture', 'events') }}`. |
| `dbt/seeds/genre_family_map.csv` | Static mapping: `event_type` → `genre_family`. Replaces the `GENRE_FAMILY_MAP` Python dict — source of truth is now in the warehouse and version-controlled. Reload with `dbt seed` after changes. |

### Staging layer (views)

| File | Role |
|------|------|
| `stg_events.sql` | `SELECT *` from `events`, filters `title IS NOT NULL AND event_date IS NOT NULL` |
| `stg_events.yml` | Schema tests: `signature` not_null + unique; `title`, `event_date`, `source` not_null. Pipeline halts here on failure. |
| `stg_movies.sql` | `SELECT *` from `movies`; wraps `genres` in `NULLIF(TRIM(...), '')` to convert whitespace-only strings to proper NULLs |
| `stg_movies.yml` | `signature` and `title` not_null + unique |

### Intermediate layer (views — business logic)

| File | Role |
|------|------|
| `int_events.sql` | LEFT JOINs `stg_events` ← `genre_family_map` (case-insensitive on `event_type`). Adds `price_bucket` column: Gratuit / < 10€ / 10-20€ / 20€+. Downstream marts just `SELECT *`. |
| `int_movies.sql` | Deduplicates genres: `STRING_TO_ARRAY → UNNEST → DISTINCT TRIM → STRING_AGG` alphabetically. Prevents "Drama, Drama" duplicates from repeated Wikipedia lookups. |

### Marts (tables)

| File | Role |
|------|------|
| `fct_concerts.sql` | `SELECT * FROM int_events WHERE event_date >= CURRENT_DATE - 1 ORDER BY event_date`. The UI and any future BI tool reads this directly. |
| `fct_films.sql` | `SELECT * FROM int_movies WHERE release_date IS NOT NULL ORDER BY release_date` |

### Tests and macros

| File | Role |
|------|------|
| `dbt/tests/assert_min_price_lte_max_price.sql` | **Singular test**: returns rows where `min_price > max_price`. Any row = test fails = DAG fails before mart rebuild. Guards against scraper bugs writing inverted prices. |
| `dbt/macros/normalize_genre.sql` | Reusable Jinja macro: INITCAP first word, LOWER the rest. Not yet wired to a model — reserved for when genre normalisation becomes a multi-model concern. |

### Spark

| File | Role |
|------|------|
| `spark/jobs/wikipedia_genre_enrichment.py` | Fetches `movies WHERE genres IS NULL`. Parallelises across 4 partitions (`numSlices=4`). Each partition opens its own psycopg2 connection, calls `fetch_wikipedia_genres()` (imported from `scrapers/ecrantotal_pipeline.py`), sleeps 1–1.5 s between calls, commits. Runs `local[4]` — no separate cluster needed. |

---

## The migration SQL — purpose and future use

`sql/003_cleanup_genres_and_prices.sql` is kept as a **reusable recovery script**, not a
one-time artefact. SQL migrations are numbered and never deleted — they document the full
history of schema and data corrections, just as git commits document code changes.

Concrete future uses:

1. **New dirty genres** — a future scraper run introduces bad values. Re-run Part 1 (the
   CTE + UPDATE) to strip anything not in the whitelist. No code change needed.
2. **New genre added to `_GENRE_KEYWORDS`** — update the `valid_genres` list in the SQL
   to match, re-run to back-fill existing rows.
3. **New free-label type** added to the price scraper — run Part 2 to reset prices, then
   re-trigger `dag_bdxc_prices` (exactly what was done when `free_label` was added).
4. **New environment** — a freshly restored DB dump can be normalised to a known-good
   state by running the full migration sequence: `001_` → `002_` → `003_`.
5. **Future dbt test** — `dbt-expectations` has `expect_column_values_to_be_in_set`. The
   SQL in this file is the reference logic for writing that test formally.
