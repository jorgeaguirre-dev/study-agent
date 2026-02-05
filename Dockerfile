# Imagen base oficial de Python
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de requerimientos y el script al contenedor
COPY requirements.txt .
COPY process_images.py .

# Instala las dependencias.
# google-cloud-storage es para listar los archivos en GCS.
RUN pip install --no-cache-dir -r requirements.txt

# Comando para ejecutar el script cuando se inicia el contenedor
# (El contenedor debe terminar cuando se complete la tarea)
ENTRYPOINT ["python", "process_images.py"]