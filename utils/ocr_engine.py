# utils/ocr_engine.py
import io
import requests
from PIL import Image
import pytesseract


def extract_text_from_url(img_url: str, lang: str = "fra") -> str:
    """
    Télécharge une image depuis une URL et extrait le texte via Tesseract.
    """
    try:
        print(f"[OCR] Téléchargement : {img_url}")
        response = requests.get(img_url, timeout=10)
        response.raise_for_status()  # Erreur si 404 ou 500

        img = Image.open(io.BytesIO(response.content))

        # Prétraitement de base (Noir et Blanc) pour aider Tesseract
        img = img.convert("L")

        text = str(pytesseract.image_to_string(img, lang=lang))
        return text.strip()

    except Exception as e:
        print(f"[OCR] Erreur critique : {e}")
        return ""
