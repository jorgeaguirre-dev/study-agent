import os
from google.cloud import storage
from google import genai
from google.genai import types

# ----------------- ENVIRONMENT CONFIGURATION -----------------
# These variables will be injected from the Cloud Run or Cloud Build environment.
PROJECT_ID = os.environ.get("GCP_PROJECT")
LOCATION = os.environ.get("GCP_REGION")
INPUT_BUCKET = os.environ.get("INPUT_BUCKET")
OUTPUT_BUCKET = os.environ.get("OUTPUT_BUCKET")
MODEL_NAME = os.environ.get("MODEL_NAME")

if not INPUT_BUCKET:
    raise EnvironmentError(f"The INPUT_BUCKET environment variable is not configured: {INPUT_BUCKET}")
if not OUTPUT_BUCKET:
    raise EnvironmentError(f"The OUTPUT_BUCKET environment variable is not configured: {OUTPUT_BUCKET}")
if not MODEL_NAME:
    raise EnvironmentError(f"The MODEL_NAME environment variable is not configured: {MODEL_NAME}")


def load_prompt():
    # 1. Defining the names of the files
    original = "system_prompt.txt"
    example = "system_prompt.txt.example"
    
    # 2. Searching for the files
    if os.path.exists(original):
        path = original
    elif os.path.exists(example):
        print(f"⚠️ Warning: Using {example} because {original} does not exist.")
        path = example
    else:
        raise FileNotFoundError(f"Neither {original} nor {example} was found")

    with open(path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def process_images_from_gcs_batch():
    """
    Lists images in the GCS bucket and processes them using the Gemini API in Vertex AI.
    """
    
    # 1. Client Initialization
    # Cloud Run uses the default Service Account credentials.
    storage_client = storage.Client(project=PROJECT_ID)
    
    # The Gemini/Vertex AI client.
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )

    # 2. System Instruction (The Tutor Agent)
    system_instruction = load_prompt()

    # 3. Model Configuration (Adjusted for factual responses)
    generate_content_config = types.GenerateContentConfig(
        temperature = 0.2,
        top_p = 0.95,
        max_output_tokens = 2048,
        system_instruction = system_instruction,
        # Keeping safety settings low as requested
        safety_settings = [
            types.SafetySetting(category=cat, threshold="BLOCK_NONE") 
            for cat in ["HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_DANGEROUS_CONTENT", 
                        "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_HARASSMENT"]
        ],
    )
    
    print(f"--- Starting batch processing of images in gs://{INPUT_BUCKET} ---")
    
    try:
        bucket = storage_client.bucket(INPUT_BUCKET)
        blobs = bucket.list_blobs()
    except Exception as e:
        print(f"Error connecting to or listing the bucket: {e}")
        return

    # 4. Process each image
    for blob in blobs:
        # 1. Define output filename (as you did at the end)
        base_name = os.path.splitext(blob.name)[0]
        sanitized_name = base_name.replace('.', '_').replace('/', '_')
        filename = f"result_{sanitized_name}.md"

        # Filter only image files
        if not blob.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) or blob.name.endswith('/'):
            print(f"Skipping non-image file: {blob.name}")
            continue

        # 2. Check if output file ALREADY EXISTS
        output_blob = storage_client.bucket(OUTPUT_BUCKET).blob(filename)

        if output_blob.exists():
                print(f"Skipping {blob.name}: Output file {filename} already exists.")
                continue # <-- Go to next file in loop

        # 3. Build current input image uri and Process the image
        gcs_uri = f"gs://{INPUT_BUCKET}/{blob.name}"
        # print(f"\n====================================================================================")
        print(f"| Processing: {blob.name} | URI: {gcs_uri}")
        # print(f"====================================================================================")
        
        try:
            # Reference to file in GCS
            image_part = types.Part.from_uri(
                file_uri=gcs_uri,
                mime_type=f"image/{blob.name.split('.')[-1].replace('jpg', 'jpeg')}"
            )
            
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        image_part,
                        types.Part.from_text(text="Analyze this question and follow the system instructions.")
                    ]
                )
            ]

            # Model call, using streaming for output in case it's long
            print("--- Gemini Response ---")
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=generate_content_config,
            )

            # print(response.text)
            if OUTPUT_BUCKET:
                # Save
                # output_blob.upload_from_string(response.text.encode('utf-8'))
                output_blob.upload_from_string(
                    data=response.text.encode('utf-8'),
                    content_type='text/markdown; charset=UTF-8'
                )
                print(f"Markdown result: gs://{OUTPUT_BUCKET}/{filename}")
            else:
                print("Warning: OUTPUT_BUCKET_NAME not defined. Result is only in logs.")
            
        except Exception as e:
            print(f"Error processing image {blob.name}: {e}")

# Main call to function when container runs
if __name__ == "__main__":
    process_images_from_gcs_batch()