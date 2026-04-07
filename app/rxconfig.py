import reflex as rx
import os
from dotenv import load_dotenv

load_dotenv()
# On récupère l'URL de la DB depuis l'environnement ou on met une valeur par défaut
# Format : postgresql://user:password@host:port/dbname
raw_url: str = os.getenv("POSTGRES_URL", "")

db_url: str = str(raw_url)

if "db_postgres" in raw_url and not os.path.exists("/.dockerenv"):
    db_url = db_url.replace("db_postgres", "localhost")

config = rx.Config(
    app_name="app",
    db_url=db_url,
)
