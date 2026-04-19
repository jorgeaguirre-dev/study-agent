# Official Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and the script into the container
COPY requirements.txt .
COPY process_images.py .

# Install dependencies.
# google-cloud-storage is used to list files in GCS.
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the script when the container starts
# (The container should terminate when the task is complete)
ENTRYPOINT ["python", "process_images.py"]