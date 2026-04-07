FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install poetry && poetry install

# Reflex a besoin de ces ports
EXPOSE 3000 8000

CMD ["poetry", "run", "reflex", "run", "--env", "prod"]
