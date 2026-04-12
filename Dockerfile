FROM apache/airflow:2.10.2-python3.12

USER root
# Installation des dépendances système (Java + Tesseract + Playwright Chromium)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jdk \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-fra \
    libgl1-mesa-glx \
    # Chromium deps for Playwright
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2 libatspi2.0-0 \
    libx11-6 libxext6 libxcb1 libxshmfence1 fonts-liberation && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create shared Playwright browser dir accessible by any user
RUN mkdir -p /opt/playwright-browsers && chmod 777 /opt/playwright-browsers
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers

USER airflow
# Installation des libs Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Install Playwright Chromium browser into the shared path
RUN python -m playwright install chromium
