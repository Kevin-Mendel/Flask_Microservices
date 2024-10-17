# Basis-Image mit Python
FROM python:3.11-slim

# Arbeitsverzeichnis im Container festlegen
WORKDIR /app

# Kopiere die requirements.txt in das Container-Verzeichnis
COPY requirements.txt .

# Installiere die Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere die app.py in das Container-Verzeichnis
COPY app.py .

# Exponiere den Port, auf dem die Flask-App läuft
EXPOSE 5000

# Befehl zum Starten der Flask-App
CMD ["python", "app.py"]