FROM python:3.12-slim

WORKDIR /app

# 1. Install outils système (indispensable pour pkill et reflex)
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

# 2. Copie du config Python
COPY pyproject.toml poetry.lock* /app/

# 3. Install sans venv
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# 4. Injection de l'URL pour le frontend
ARG API_URL
ENV API_URL=$API_URL

# 5. Copie de tout le projet
COPY app/ /app/


EXPOSE 3000 8000

CMD ["reflex", "run", "--env", "prod"]
