# Usa una imagen base oficial de Python
FROM python:3.13.3-bookworm

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de requisitos y el código fuente al contenedor
COPY requirements.txt ./
COPY . .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto en el que se ejecutará la aplicación
EXPOSE 8000

# Comando por defecto para ejecutar la aplicación
CMD ["chainlit", "run", ,"-h", "app.py", "--host", "0.0.0.0", "--port", "8000"]
