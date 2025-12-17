import os
from google.cloud import storage
from google import genai
from google.genai import types

# ----------------- CONFIGURACIÓN DEL ENTORNO -----------------
# Estas variables se inyectarán desde el entorno de Cloud Run o Cloud Build.
PROJECT_ID = os.environ.get("GCP_PROJECT")
LOCATION = os.environ.get("GCP_REGION", "us-central1")
INPUT_BUCKET = os.environ.get("INPUT_BUCKET_NAME")
OUTPUT_BUCKET = os.environ.get("OUTPUT_BUCKET_NAME")
MODEL_NAME = "gemini-2.5-flash"

if not INPUT_BUCKET:
    raise EnvironmentError(f"La variable de entorno INPUT_BUCKET_NAME no está configurada: {INPUT_BUCKET}")

def process_images_from_gcs_batch():
    """
    Lista las imágenes en el bucket de GCS y las procesa usando la API de Gemini en Vertex AI.
    """
    
    # 1. Inicialización de Clientes
    # Cloud Run usa las credenciales de la Cuenta de Servicio por defecto.
    storage_client = storage.Client(project=PROJECT_ID)
    
    # El cliente de Gemini/Vertex AI.
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )

    # 2. Instrucción de Sistema (El Agente Tutor)
    system_instruction = (
    "Eres un tutor experto y un especialista en Google Cloud, enfocado en la certificación Associate Cloud Engineer (ACE). "
    "Tu respuesta **DEBE ESTAR COMPLETAMENTE FORMATEADA EN MARKDOWN**, utilizando encabezados (`#`, `##`) y listas para máxima legibilidad. "
    "Tu tarea es analizar la imagen proporcionada, que contiene una pregunta de examen. "
    " En las mismas preguntas, se suele resaltar con color distinto la respuesta correcta; pero no siempre es así. "
    "Para cada imagen, debes realizar los siguientes pasos en el siguiente formato Markdown: "
    "**# [Número de Pregunta o Título]**"
    "**## 1. Transcripción**"
    "Escribe la pregunta y las opciones de respuesta tal como aparecen en la imagen (usa una lista numerada para las opciones). "
    "**## 2. Respuesta Correcta**"
    "Indica claramente la opción correcta en **negritas**."
    "**## 3. Explicación Detallada (GCP Tutor)**"
    "Proporciona una explicación concisa y precisa basada en la documentación y las mejores prácticas de Google Cloud, justificando la respuesta correcta y por qué las otras opciones son incorrectas."
    "Tu respuesta debe ser directa y solo contener la información de estudio solicitada."
    "Añade algún link relevante a la documentación oficial de Google Cloud para referencia adicional."
    "Al final del documento, añade una línea con la etiqueta 'REFERENCIA_PDF:' "
    "indicando el tema principal de la pregunta (ej. GKE, VPC, IAM, BigQuery). "
    "EJEMPLO: REFERENCIA_PDF: VPC"
)
    
    # 3. Configuración del Modelo (Ajustada para respuestas factuales)
    generate_content_config = types.GenerateContentConfig(
        temperature = 0.2,
        top_p = 0.95,
        max_output_tokens = 2048,
        system_instruction = system_instruction,
        # Manteniendo las configuraciones de seguridad bajas según lo solicitado
        safety_settings = [
            types.SafetySetting(category=cat, threshold="BLOCK_NONE") 
            for cat in ["HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_DANGEROUS_CONTENT", 
                        "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_HARASSMENT"]
        ],
    )
    
    print(f"--- Iniciando el procesamiento por lotes de imágenes en gs://{INPUT_BUCKET} ---")
    
    try:
        bucket = storage_client.bucket(INPUT_BUCKET)
        blobs = bucket.list_blobs()
    except Exception as e:
        print(f"Error al conectar o listar el bucket: {e}")
        return

    # 4. Procesar cada imagen
    for blob in blobs:
        # 1. Definir el nombre del archivo de salida (como lo hiciste al final)
        base_name = os.path.splitext(blob.name)[0]
        sanitized_name = base_name.replace('.', '_').replace('/', '_')
        filename = f"result_{sanitized_name}.md"

        # Filtrar solo archivos de imagen
        if not blob.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) or blob.name.endswith('/'):
            print(f"Saltando archivo no imagen: {blob.name}")
            continue

        # 2. Verificar si el archivo de salida YA EXISTE
        output_blob = storage_client.bucket(OUTPUT_BUCKET).blob(filename)

        if output_blob.exists():
                print(f"Skipping {blob.name}: Output file {filename} already exists.")
                continue # <-- Ir al siguiente archivo en el bucle

        # 3. Armo uri de actual input image y Procesar la imagen
        gcs_uri = f"gs://{INPUT_BUCKET}/{blob.name}"
        # print(f"\n====================================================================================")
        print(f"| Procesando: {blob.name} | URI: {gcs_uri}")
        # print(f"====================================================================================")
        
        try:
            # Referencia al archivo en GCS
            image_part = types.Part.from_uri(
                file_uri=gcs_uri,
                mime_type=f"image/{blob.name.split('.')[-1].replace('jpg', 'jpeg')}"
            )
            
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        image_part,
                        types.Part.from_text(text="Analiza esta pregunta de certificación y sigue las instrucciones de sistema.")
                    ]
                )
            ]

            # Llamada al modelo, usando streaming para el output por si es largo
            print("--- Respuesta de Gemini ---")
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=generate_content_config,
            )

            # print(response.text)
            if OUTPUT_BUCKET:
                # Guardado
                # output_blob.upload_from_string(response.text.encode('utf-8'))
                output_blob.upload_from_string(
                    data=response.text.encode('utf-8'),
                    content_type='text/markdown; charset=UTF-8'
                )
                print(f"Resultado en Markdown: gs://{OUTPUT_BUCKET}/{filename}")
            else:
                print("Advertencia: OUTPUT_BUCKET_NAME no definido. El resultado solo está en los logs.")
            
        except Exception as e:
            print(f"Error al procesar la imagen {blob.name}: {e}")

# Llamada principal a la función cuando el contenedor se ejecuta
if __name__ == "__main__":
    process_images_from_gcs_batch()