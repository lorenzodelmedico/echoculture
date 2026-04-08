FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl unzip && rm -rf /var/lib/apt/lists/*
RUN pip install poetry

COPY pyproject.toml poetry.lock* /app/

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY app/ /app/

EXPOSE 3000 8000

CMD ["reflex", "run", "--env", "prod"]
