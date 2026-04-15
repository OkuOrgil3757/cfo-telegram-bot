FROM python:3.11-slim

WORKDIR /app

# Install system deps for matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure data directory exists for SQLite
RUN mkdir -p data

CMD ["python", "bot.py"]
