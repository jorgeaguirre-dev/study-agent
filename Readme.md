

```bash
# Variables del Proyecto
export PROJECT_ID="gen-lang-client-0664334117"
export REGION="us-central1"

# Variables de la Imagen (Artifact Registry)
export REPOSITORY_NAME="ace-tutor"
export IMAGE_NAME="ace-tutor-agent"

# Variables del Job de Cloud Run
export JOB_NAME="ace-image-processor"
export SERVICE_ACCOUNT_EMAIL="ace-tutor-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Variables de la Aplicación (Buckets)
export BUCKET_DE_ENTRADA="vertex-ia-251213"
export BUCKET_DE_SALIDA="ia-results"

gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/${IMAGE_NAME}


# Nota: Usamos --update-env-vars si el job ya existe, o --set-env-vars si es nuevo.
# Si el job ya existe (solo tienes que actualizar las variables):
gcloud run jobs update ${JOB_NAME} \
    --region ${REGION} \
    --service-account ${SERVICE_ACCOUNT_EMAIL} \
    --update-env-vars INPUT_BUCKET_NAME=${BUCKET_DE_ENTRADA},OUTPUT_BUCKET_NAME=${BUCKET_DE_SALIDA}

# Si el job no existe (primer despliegue completo):
# gcloud run jobs create ${JOB_NAME} \
#     --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/${IMAGE_NAME} \
#     --region ${REGION} \
#     --service-account ${SERVICE_ACCOUNT_EMAIL} \
#     --set-env-vars INPUT_BUCKET_NAME=${BUCKET_DE_ENTRADA},OUTPUT_BUCKET_NAME=${BUCKET_DE_SALIDA} \
#     --max-retries 0

gcloud run jobs execute ${JOB_NAME} --region ${REGION}
```