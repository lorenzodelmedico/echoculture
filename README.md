# SynkOS

Agrégateur de sorties culturelles à Bordeaux — concerts, spectacles, expositions et films, au même endroit.

🌐 **[synkos.mosaik-project.com](https://synkos.mosaik-project.com)**

---

## Ce que tu y trouveras

| Onglet | Contenu |
|--------|---------|
| **Aujourd'hui** | Tout ce qui se passe aujourd'hui (événements + sorties ciné) |
| **Concerts** | Agenda concerts de la métropole bordelaise |
| **Spectacles** | Théâtre, cirque, opéra, comédie musicale… |
| **Expos** | Expositions en cours |
| **Films** | Sorties cinéma de la semaine |

Les données sont mises à jour automatiquement chaque semaine.

---

## Installer l'application sur ton appareil

SynkOS est une **Progressive Web App (PWA)** — on ne la trouvera pas sur l'App Store ou le Play Store.

### 📱 iPhone / iPad (Safari)

1. Ouvre [synkos.mosaik-project.com](https://synkos.mosaik-project.com) dans **Safari**
2. Appuie sur l'icône **Partager** (carré avec une flèche vers le haut) en bas de l'écran
3. Fais défiler et sélectionne **« Sur l'écran d'accueil »**
4. Confirme en appuyant sur **Ajouter**

> L'app apparaît sur ton écran d'accueil comme une vraie application, en plein écran.

---

### 🤖 Android (Chrome)

1. Ouvre [synkos.mosaik-project.com](https://synkos.mosaik-project.com) dans **Chrome**
2. Appuie sur les **trois points** en haut à droite
3. Sélectionne **« Ajouter à l'écran d'accueil »** ou **« Installer l'application »**
4. Confirme

> Sur certains appareils, une bannière d'installation apparaît directement en bas de l'écran.

---

### 💻 Desktop — Chrome / Edge / Brave

1. Ouvre [synkos.mosaik-project.com](https://synkos.mosaik-project.com)
2. Clique sur l'icône **installer** (➕ ou écran avec flèche) dans la barre d'adresse à droite
3. Clique sur **Installer**

> L'app s'ouvre dans sa propre fenêtre, sans barre de navigation du navigateur.

**Edge :** Menu (···) → **Applications** → **Installer ce site en tant qu'application**

---

### 🦊 Firefox (Android)

1. Ouvre le site dans Firefox
2. Menu (trois points) → **Installer**

> Firefox Desktop ne supporte pas l'installation PWA nativement.

---

## À propos

Projet hobby personnel. Sources : [junklive.fr](https://www.junklive.fr) (événements Bordeaux) et Écran Total (sorties ciné).

[GitHub](https://github.com/lorenzodelmedico) · [Malt](https://www.malt.fr/profile/lorenzodelmedico)

---

## Self-hosting

Want to run your own instance? Everything ships in a single `docker compose` stack: Postgres + MongoDB + Airflow + dbt + Spark + Ollama + the Reflex UI.

### Prerequisites

- A Linux server (or local machine) with at least **8 GB RAM** and **20 GB disk** free.
- [Docker Engine](https://docs.docker.com/engine/install/) **24+** and the Compose v2 plugin (`docker compose`, not the old `docker-compose`).
- A domain name if you want public HTTPS access. Not needed for local-only use.

### 1. Clone & configure

```bash
git clone https://github.com/lorenzodelmedico/echoculture.git synkos
cd synkos
cp .env.example .env
```

Open `.env` and fill in the values. Bare minimum to get the app running locally:

| Variable | What to set |
|----------|------------|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Whatever you want — used by the Postgres container at first boot |
| `POSTGRES_URL` | Must match the three above: `postgresql://USER:PASSWORD@db_postgres:5432/DB` |
| `MONGO_INITDB_ROOT_PASSWORD` / `MONGO_URL` | Same idea for MongoDB |
| `AIRFLOW_SECRET_KEY` | Run `python -c "import secrets; print(secrets.token_hex(32))"` |
| `FRONTEND_URL` / `BACKEND_URL` / `API_URL` | `http://localhost:3000` / `http://localhost:8000` for local; your public URLs for production |

The other vars (Cloudflare token, Discord webhook, etc.) are optional — see the comments in `.env.example`.

### 2. Bootstrap

```bash
./setup.sh
```

This builds the images, brings the stack up, and prints the useful URLs. Re-running is safe.

You should now have:

| Service | URL | Purpose |
|---------|-----|---------|
| **App** | http://localhost:3000 | The Reflex UI |
| **Airflow** | http://localhost:8080 | DAG scheduler (login: `admin` / `admin`) |
| **Adminer** | http://localhost:8082 | Postgres web client |
| **Mongo Express** | http://localhost:8081 | Mongo web client |

The DB is empty until you run a scrape. Trigger one from the Airflow UI (e.g. `scraper_bdxc_mongodb_to_pg`) or via CLI:

```bash
docker exec echoculture-airflow-scheduler-1 \
  airflow dags trigger scraper_bdxc_mongodb_to_pg
```

### 3. Expose it publicly

You have two paths. Pick one.

#### Option A — Your own reverse proxy (recommended)

The compose stack publishes the UI on host port `3000`. Point your existing nginx / caddy / traefik at it and terminate TLS there.

Minimal Caddy example:
```caddyfile
synkos.example.com {
    reverse_proxy localhost:3000
}
api.synkos.example.com {
    reverse_proxy localhost:8000
}
```

Then in `.env`:
```
FRONTEND_URL=https://synkos.example.com
BACKEND_URL=https://api.synkos.example.com
API_URL=https://api.synkos.example.com
```

Restart the UI to pick up the new URLs:
```bash
docker compose up -d --build echoculture-ui
```

#### Option B — Cloudflare Tunnel

No open ports on your server. Cloudflare proxies traffic to a daemon that lives inside the compose stack.

1. Sign in to [Cloudflare Zero Trust](https://one.dash.cloudflare.com) → **Networks** → **Tunnels** → **Create a tunnel**.
2. Public hostnames:
   - `synkos.example.com` → `http://echoculture-ui:3000`
   - `api.synkos.example.com` → `http://echoculture-ui:8000`
3. Copy the tunnel token into `.env` as `CLOUDFLARE_TUNNEL_TOKEN`.
4. Set `FRONTEND_URL` / `BACKEND_URL` / `API_URL` to your Cloudflare hostnames.
5. Start the stack with the cloudflare profile enabled:

```bash
docker compose --profile cloudflare up -d --build
```

The `cloudflared` service is gated behind a profile so it only runs when you opt in — friends without a Cloudflare account can ignore it entirely.

### Updating

```bash
git pull
docker compose up -d --build
```

`docker compose down -v` wipes the database volumes — only do that if you really want to reset.

### Troubleshooting

- **`Error: env_file .env not found`** — you skipped `cp .env.example .env`.
- **`POSTGRES_URL` connection refused** — the host part must be `db_postgres` (the compose service name), not `localhost`.
- **Airflow tasks fail with `ModuleNotFoundError`** — rebuild after editing `requirements.txt`: `docker compose up -d --build airflow-webserver airflow-scheduler`.
- **UI loads but shows no events** — no scrape has run yet. Trigger a DAG from Airflow.

For day-to-day operations (dbt commands, secret rotation, dependency updates) see [`MAINTENANCE.md`](MAINTENANCE.md). For a tour of the data flow (Mongo → Postgres → dbt → UI) see [`ARCHITECTURE.md`](ARCHITECTURE.md).
