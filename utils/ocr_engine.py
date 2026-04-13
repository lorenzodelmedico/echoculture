import io
import logging
import requests
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)


def extract_text_from_url(img_url: str, lang: str = "fra") -> str:
    try:
        logger.debug(f"[OCR] Téléchargement : {img_url}")
        response = requests.get(img_url, timeout=10)
        response.raise_for_status()

        img = Image.open(io.BytesIO(response.content))
        img = img.convert("L")

        text = str(pytesseract.image_to_string(img, lang=lang))
        return text.strip()

    except Exception as e:
        logger.error(f"[OCR] Erreur critique : {e}")
        return ""
