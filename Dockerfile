# Base image
FROM python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Instala dependências do sistema que ajudam a compilar pacotes nativos
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    ffmpeg \
    libsndfile1 \
 && rm -rf /var/lib/apt/lists/*

# Garante que o pip esteja atualizado com ferramentas de build
RUN pip install --upgrade pip setuptools wheel build

# Copia pyproject.toml e instala dependências
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copia restante da aplicação
COPY . .

# Expõe porta
EXPOSE 8000

# Comando de entrada
CMD ["gunicorn", "app:app"]
