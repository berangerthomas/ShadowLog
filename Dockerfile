# Utilisation de l'image Python 3.12 comme base
FROM python:3.11-slim

# Définition du répertoire de travail
WORKDIR /app

# Copie des fichiers de dépendances
COPY requirements.txt .

# Installation des dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copie de tout le contenu du projet dans le conteneur
COPY . .

# Exposition du port 8501 (port par défaut de Streamlit)
EXPOSE 8501

# Commande pour démarrer l'application Streamlit
CMD ["streamlit", "run", "app.py"]