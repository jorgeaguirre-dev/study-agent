# pip install google-genai google-cloud-storage

# test_api.py
import os
from google.genai import types

# Define la URI de prueba (asumiendo que ya renombraste el archivo)
GCS_URI_TEST = "gs://gen-lang-client-0664334117/Screenshot_2025-12-13_200740.png"
MIME_TYPE_TEST = "image/png"

print(f"Probando Part.from_uri() con: {GCS_URI_TEST} y {MIME_TYPE_TEST}")

try:
    # Intenta la configuración que el error sugiere (1 posicional, 1 keyword)
    image_part = types.Part.from_uri(
        GCS_URI_TEST,
        mime_type=MIME_TYPE_TEST
    )
    print("\n✅ Éxito! El formato Part.from_uri(uri, mime_type=mime) es correcto.")

except TypeError as e:
    if "takes 1 positional argument" in str(e):
        # Intentar la sintaxis que no tiene argumentos nombrados (Ejemplo 1 de la documentación)
        try:
            image_part = types.Part.from_uri(GCS_URI_TEST, MIME_TYPE_TEST)
            print("\n✅ Éxito! El formato Part.from_uri(uri, mime) es correcto.")
        except TypeError as e_pos:
            print(f"\n❌ Fallo en la sintaxis posicional: {e_pos}")

            # Intentar la sintaxis de la documentación (con 'file_uri' o 'gcs_uri')
            try:
                image_part = types.Part.from_uri(file_uri=GCS_URI_TEST, mime_type=MIME_TYPE_TEST)
                print("\n✅ Éxito! El formato Part.from_uri(file_uri=uri, mime_type=mime) es correcto.")
            except TypeError as e_keyword:
                 print(f"\n❌ Fallo en la sintaxis de palabra clave: {e_keyword}")

                 # Intentar el constructor explícito (Opción de Recuperación)
                 from google.genai.types import FileData
                 file_data = types.Part.FileData(file_uri=GCS_URI_TEST, mime_type=MIME_TYPE_TEST)
                 image_part = types.Part(file_data=file_data)
                 print("\n✅ Éxito! El constructor explícito Part(file_data=FileData()) funcionó.")
                 
except Exception as e:
    print(f"\n❌ Error genérico inesperado: {e}")