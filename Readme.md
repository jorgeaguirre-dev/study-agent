# Study Agent - Complete Documentation

## 📋 Project Overview

The **Study Agent** is an automated system that analyzes exam question images (from the xxxx certification) and generates detailed explanations using Google's Gemini AI model. The system processes images in batch, extracts questions, and produces markdown-formatted study materials.

### Key Features:
- 🎯 Automated batch processing of exam question images
- 🤖 Intelligent analysis using Gemini 2.5 Flash model
- 📝 Markdown-formatted output with explanations
- ☁️ Cloud-native architecture on Google Cloud Platform
- 🔄 Duplicate prevention (skips already processed images)

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Google Cloud Platform                   │
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │  GCS INPUT   │         │ GCS OUTPUT   │                  │
│  │   BUCKET     │         │   BUCKET     │                  │
│  │ (Images)     │         │ (Markdown)   │                  │
│  └──────┬───────┘         └──────▲───────┘                  │
│         │                        │                          │
│         │   ┌──────────────────┐ │                          │
│         └──>│  Cloud Run Job   │─┘                          │
│             │  (Docker Image)  │                            │
│             │                  │                            │
│             │  Process Images  │                            │
│             │  + Gemini API    │                            │
│             └──────────────────┘                            │
│                     │                                       │
│                     ▼                                       │
│             Vertex AI / Gemini                              │
│             (LLM Analysis)                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Input Phase**: Exam question images are uploaded to the `INPUT_BUCKET`
2. **Processing Phase**: Cloud Run Job starts the containerized application
3. **Analysis Phase**: For each image:
   - Load Gemini model with system prompt (tutor instructions)
   - Send image + prompt to Gemini 2.5 Flash model
   - Model returns markdown-formatted analysis
4. **Output Phase**: Results saved as `result_*.md` files to `OUTPUT_BUCKET`

---

## 🚀 Quick Start

### Prerequisites

- Google Cloud Project with:
  - Cloud Run API enabled
  - Artifact Registry API enabled
  - Vertex AI API enabled
  - Two GCS buckets (input and output)
  - Service Account with appropriate permissions

- Local tools:
  - `gcloud` CLI installed and configured
  - Docker installed (for building images locally)
  - Python 3.11+ (for local testing)

### Environment Setup

1. **Create `.env` file** in the project root:

```bash
# GCP Configuration
PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
REPOSITORY_NAME="study-agent"
IMAGE_NAME="process-images"
JOB_NAME="study-agent-job"
SERVICE_ACCOUNT_EMAIL="your-sa@your-project.iam.gserviceaccount.com"

# GCS Buckets
INPUT_BUCKET="input-exam-images"
OUTPUT_BUCKET="output-study-materials"

# Model Variables
MODEL_NAME="gemini-1.5-pro"
```

2. **Load environment variables**:

```bash
export REPO_FOLDER=${PWD}
set -o allexport && source .env && set +o allexport
```

---

## 🐳 Docker & Deployment

### Docker Image Build & Push

The Dockerfile creates a lightweight containerized application using Python 3.11-slim:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
COPY process_images.py .
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python", "process_images.py"]
```

**Build and push to Artifact Registry**:

```bash
gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/${IMAGE_NAME}
```

### Cloud Run Job Deployment

**First-time deployment** (create new job):

```bash
gcloud run jobs create ${JOB_NAME} \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/${IMAGE_NAME} \
    --region ${REGION} \
    --service-account ${SERVICE_ACCOUNT_EMAIL} \
    --set-env-vars \
      GCP_PROJECT=${PROJECT_ID},\
      GCP_REGION=${REGION},\
      INPUT_BUCKET_NAME=${INPUT_BUCKET},\
      OUTPUT_BUCKET_NAME=${OUTPUT_BUCKET} \
    --max-retries 0
```

**Update environment variables** (if job already exists):

```bash
gcloud run jobs update ${JOB_NAME} \
    --region ${REGION} \
    --service-account ${SERVICE_ACCOUNT_EMAIL} \
    --update-env-vars \
      INPUT_BUCKET_NAME=${INPUT_BUCKET},\
      OUTPUT_BUCKET_NAME=${OUTPUT_BUCKET}
```

**Execute the job**:

```bash
gcloud run jobs execute ${JOB_NAME} --region ${REGION} --task-timeout 1200s
```

---

## 📝 Code Structure

### `process_images.py`

**Purpose**: Main processing script that orchestrates image analysis

**Key Functions**:

#### `load_prompt()`
- Loads the system instruction from `system_prompt.txt`
- Falls back to `system_prompt.txt.example` if original doesn't exist
- Returns the tutor agent instructions as a string

#### `process_images_from_gcs_batch()`
- **Client Initialization**: Creates GCS and Gemini API clients
- **Configuration**: Sets up model parameters:
  - Model: `gemini-2.5-flash`
  - Temperature: 0.2 (low randomness for consistent answers)
  - Max tokens: 2048
  - Safety settings: Set to BLOCK_NONE for educational content
- **Image Processing Loop**:
  - Lists all objects in INPUT_BUCKET
  - Filters for image files (`.png`, `.jpg`, `.jpeg`, `.webp`)
  - Checks if output already exists (prevents reprocessing)
  - Sends image + system prompt to Gemini API
  - Saves markdown results to OUTPUT_BUCKET

### `system_prompt.txt`

Contains the tutor agent instructions, defining:
- Response format (Markdown)
- Analysis structure (Transcription, Correct Answer, Detailed Explanation)
- References to documentation
- Output labeling (REFERENCIA_PDF tag)

### `requirements.txt`

Dependencies:
- `google-cloud-storage`: For GCS bucket operations
- `google-genai`: Gemini API client (includes Vertex AI support)

---

### Install Dependencies Locally

```bash
pip install -r requirements.txt
```

## 🔐 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GCP_PROJECT` | Google Cloud Project ID | `my-project-123` |
| `GCP_REGION` | GCP region for deployment | `us-central1` |
| `INPUT_BUCKET_NAME` | GCS bucket for input images | `gs://exam-questions` |
| `OUTPUT_BUCKET_NAME` | GCS bucket for markdown output | `gs://study-materials` |

---

## 📊 Processing Workflow

### Single Image Processing Flow

```
1. List blobs in INPUT_BUCKET
   ↓
2. For each blob:
   ├─ Is it an image file? (png, jpg, jpeg, webp)
   │  └─ If No: Skip and continue
   │
   ├─ Does output file exist?
   │  └─ If Yes: Skip and continue
   │
   ├─ Load image from GCS URI
   │  └─ gs://input-bucket/image-name.jpg
   │
   ├─ Create Gemini request with:
   │  ├─ System prompt (tutor instructions)
   │  ├─ Image content
   │  └─ Analysis request text
   │
   ├─ Call Gemini model
   │  └─ Returns markdown analysis
   │
   └─ Upload result to OUTPUT_BUCKET
      └─ result_sanitized-name.md
```

### Output File Naming

Input: `question_001.jpg`
Output: `result_question_001.md`

The system sanitizes filenames by:
- Converting dots to underscores
- Converting slashes to underscores
- Removing extensions
- Prefixing with `result_`

---

---

## 📚 Output Format

Each generated markdown file follows this structure:

```markdown
# [Question Number/Title]

## 1. Transcription
[Original question text and options]

## 2. Correct Answer
**[Correct option letter and text]**

## 3. Detailed Explanation (Tutor)
[Comprehensive explanation with reference to different docs]

REFERENCIA_PDF: [Topic like x1,x2, x3]
```

---

## 🔄 Monitoring & Troubleshooting

### Check Job Status

```bash
gcloud run jobs describe ${JOB_NAME} --region ${REGION}
```

### View Job Execution Logs

```bash
gcloud run jobs logs read ${JOB_NAME} --region ${REGION} --limit 50
```

### Common Issues

| Issue | Solution |
|-------|----------|
| INPUT_BUCKET not found | Verify bucket name and service account permissions |
| No images processed | Check image format and bucket contents |
| Output files not created | Verify OUTPUT_BUCKET exists and is writable |
| Gemini API errors | Ensure Vertex AI API is enabled and quota available |

---

## 📎 References

- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Vertex AI Gemini API](https://cloud.google.com/vertex-ai/docs/generative-ai/learn/models)
- [Cloud Run Jobs](https://cloud.google.com/run/docs/quickstarts/jobs/create)
- [google-genai Python Library](https://github.com/googleapis/python-genai)

---

## 📌 Notes

> The `google-genai` library automatically includes Vertex AI dependencies. It's designed specifically for interacting with the Gemini API within Google Cloud environment.

> Cloud Run Jobs are ideal for batch processing tasks. Unlike Cloud Run services, jobs automatically terminate after completion, reducing unnecessary costs.

> The 1200-second timeout (20 minutes) should be sufficient for processing 50-100 images depending on model response times. Adjust as needed based on volume.

---

## 📄 License

[Your License Here]

## 👤 Author

Jorge Aguirre

---

**Last Updated**: February 5, 2026
