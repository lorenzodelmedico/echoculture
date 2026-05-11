import reflex as rx
import os
from dotenv import load_dotenv
from reflex.plugins import SitemapPlugin

load_dotenv()

raw_url: str = os.getenv("POSTGRES_URL", "")
db_url: str = str(raw_url)

if "db_postgres" in raw_url and not os.path.exists("/.dockerenv"):
    db_url = db_url.replace("db_postgres", "localhost")

config = rx.Config(
    app_name="app",
    plugins=[
        SitemapPlugin(),
    ],
    title="SynkOS",
    db_url=db_url,
    env=rx.Env.PROD,
    backend_port=8000,
    frontend_port=3000,
    api_url=os.getenv("API_URL") or os.getenv("BACKEND_URL") or "http://localhost:8000",
    show_built_with_reflex=False,
)
