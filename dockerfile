# Usa una imagen base con una versión más reciente de glibc
FROM python:3.12-slim-bullseye

# Variables de entorno
ENV HOST=0.0.0.0
ENV LISTEN_PORT=8000

# Establece el directorio de trabajo
# Install system dependencies
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

# Rest of your Dockerfile (copy requirements, install Python packages, etc.)
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
COPY .env ./
COPY app.py ./  
# COPY realtime/ /app/realtime/
# COPY azure_tts.py /app/
# COPY VAD/ /app/VAD/
# COPY tools.py ./  
# Asegúrate de incluir el directorio tools

EXPOSE 8000
# Instala las dependencias de Python

# Comando para ejecutar la aplicación
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
