# Utilisez une image de base spécifique pour minimiser les mises à jour de sécurité inattendues
FROM python:3.9.10-slim-buster

# Créez un utilisateur non privilégié pour exécuter l'application
RUN useradd -r -u 1001 -g root appuser

# Créez le répertoire de travail et définissez les autorisations appropriées
WORKDIR /app
RUN chown -R appuser:root /app && chmod -R 755 /app

# Copiez uniquement les fichiers nécessaires, par exemple, en excluant les fichiers et dossiers indésirables
COPY --chown=appuser:root requirements.txt db_setup.py bot.py ./

# Passez à l'utilisateur non privilégié
USER appuser

# Installez les dépendances sans cache
RUN pip install --no-cache-dir -r requirements.txt

# Exécutez l'application en tant qu'utilisateur non privilégié
CMD ["python", "bot.py"]

FROM python:3.9-slim

WORKDIR /app

#On copy tout les ficher du document
COPY . .

#On install les API pour l'application
RUN pip install --no-cache-dir -r requirements.txt

#On install la db pour l'application
RUN python db_setup.py

#On run l'application 
CMD ["python", "bot.py"]