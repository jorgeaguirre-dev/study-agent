# Usa una imagen base oficial de Python
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de requerimientos y el script al contenedor
# Nota: La librería google-genai incluye automáticamente las dependencias de Vertex AI.
COPY requirements.txt .
COPY process_images.py .

# Instala las dependencias.
# La librería google-genai es para interactuar con la API de Gemini.
# google-cloud-storage es para listar los archivos en GCS.
RUN pip install --no-cache-dir -r requirements.txt

# Comando para ejecutar el script cuando se inicia el contenedor
# (Es importante que el contenedor termine una vez completada la tarea)
ENTRYPOINT ["python", "process_images.py"]