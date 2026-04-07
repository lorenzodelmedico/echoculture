FROM apache/airflow:2.10.2-python3.12

USER root
# Installation des dépendances système (Java + Tesseract + Bibliothèques d'image)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jdk \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-fra \
    libgl1-mesa-glx && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER airflow
# Installation des libs Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
