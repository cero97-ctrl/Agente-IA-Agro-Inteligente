# Usar una imagen base de Python oficial
FROM python:3.10-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de dependencias primero para aprovechar el cache de Docker
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación al directorio de trabajo
COPY . .

# Exponer el puerto en el que correrá la aplicación (Hugging Face usa 7860 por defecto)
EXPOSE 7860

# Comando para ejecutar la aplicación cuando el contenedor se inicie
# Usamos --host 0.0.0.0 para que sea accesible desde fuera del contenedor
CMD ["uvicorn", "web_server:app", "--host", "0.0.0.0", "--port", "7860"]