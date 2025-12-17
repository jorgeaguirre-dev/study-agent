# test_gemini_call.py

import os
from google import genai
from google.genai import types
from google.cloud import aiplatform

# --- 1. CONFIGURACIÓN DE PRUEBA ---
# Importante: Asegúrate de que este archivo exista en tu bucket y no tenga espacios
GCS_URI_TEST = "gs://vertex-ia-251213/Screenshot_2025-12-13_200740.png"
MODEL_NAME = "gemini-2.5-flash"
PROJECT_ID = "gen-lang-client-0664334117"
REGION = "us-central1"

# Inicializar Vertex AI antes de usar el cliente genai
aiplatform.init(project=PROJECT_ID, location=REGION)

# El texto que quieres que sea la guía para Gemini
SYSTEM_INSTRUCTION = (
    "Eres un experto en certificación de Google Cloud. Tu tarea es analizar "
    "la imagen de la pregunta y proporcionar una respuesta en formato Markdown "
    "que incluya: 1. El enunciado completo de la pregunta. 2. La respuesta correcta. "
    "3. Una explicación detallada de por qué esa es la respuesta correcta."
)
MIME_TYPE_TEST = "image/png"


# --- 2. PREPARACIÓN DE LA LLAMADA ---
try:
    # 2a. Crea la Parte de la imagen (usando la sintaxis 'file_uri=' que ya probamos)
    image_part = types.Part.from_uri(
        file_uri=GCS_URI_TEST,
        mime_type=MIME_TYPE_TEST
    )
    
    # 2b. Crea los contenidos (Instrucción de usuario + la imagen)
    contents = [
        types.Part.from_text(text="Analiza esta pregunta de certificación y sigue las instrucciones de sistema."),
        image_part
    ]
    
    # 2c. Crea la CONFIGURACIÓN (CLAVE: Aquí va el system_instruction)
    generate_content_config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION, # 💡 ¡La corrección va aquí!
        temperature=0.1, # Ejemplo de otro parámetro de configuración
    )
    
    # --- 3. LLAMADA A LA API ---
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=REGION
    )

    print(f"Probando generate_content con system_instruction en config...")
    
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=generate_content_config, # Pasamos la instrucción de sistema aquí dentro
        # ❌ IMPORTANTE: NO incluir 'system_instruction' como argumento aquí
    )
    
    # --- 4. RESULTADO ---
    print("\n✅ Éxito! La llamada a la API funcionó.")
    print("\n--- Respuesta de Gemini (Recortada) ---")
    print(response.text[:500] + "...")
    
except Exception as e:
    print(f"\n❌ Error durante la llamada a la API: {e}")
    print("\nPor favor, verifica si la variable 'system_instruction' está definida correctamente dentro de 'GenerateContentConfig'.")