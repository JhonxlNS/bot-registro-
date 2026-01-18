# Dockerfile - Bot Discord 100% Funcional
FROM python:3.11.9-slim-bullseye

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (para cache)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código
COPY . .

# Expor porta
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Comando de inicialização
CMD ["python", "main.py"]
