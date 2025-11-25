# Dockerfile
FROM python:3.11-slim

# Pré-requis système min (curl pour healthcheck, build deps si besoin de wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# Créer un utilisateur non-root
RUN useradd -m -u 10001 -s /usr/sbin/nologin appuser

WORKDIR /app

# Copier uniquement les requirements pour tirer profit du cache Docker
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . /app

# Droits d'écriture sur les dossiers persistants et les entrées Oxypharm
RUN mkdir -p /app/runtime_data/database /app/runtime_data/vector_db /app/inputs/Oxypharm && \
    touch /app/runtime_data/database/interactions.db && \
    chown -R appuser:appuser /app && \
    chmod 660 /app/runtime_data/database/interactions.db

USER appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

EXPOSE 8501

# Healthcheck HTTP basique sur la page d'accueil Streamlit
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://127.0.0.1:8501/ || exit 1

# Lance l'app (adapte le nom du script si besoin)
ENTRYPOINT ["python","-m","streamlit","run","MistralChat.py","--server.port=8501","--server.address=0.0.0.0"]
