# Usar una imagen base de Python oficial
FROM python:3.10-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema operativo necesarias para PyAudio, pydub, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    portaudio19-dev \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de dependencias primero para aprovechar el cache de Docker
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación al directorio de trabajo
COPY . .

# Comando para ejecutar la aplicación cuando el contenedor se inicie
# Usamos --host 0.0.0.0 para que sea accesible desde fuera del contenedor
CMD ["uvicorn", "web_server:app", "--host", "0.0.0.0", "--port", "7860"]