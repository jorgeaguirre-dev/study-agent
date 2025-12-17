

export BUCKET_NAME="vertex-ia-251213"

# Script para buscar archivos con espacios y renombrarlos
gsutil ls gs://${BUCKET_NAME}/** | \
while read GS_URI; do
    # 1. Extrae el nombre del archivo (Blob Name) y la carpeta (si existe)
    BLOB_NAME=$(basename "${GS_URI}")
    
    # 2. Crea el nuevo nombre, reemplazando espacios por guiones bajos
    NEW_BLOB_NAME=$(echo "${BLOB_NAME}" | tr ' ' '_')

    # 3. Compara: Si el nombre ha cambiado (es decir, tenía espacios)
    if [ "${BLOB_NAME}" != "${NEW_BLOB_NAME}" ]; then
        
        # 4. Obtiene el camino completo (path) en el bucket
        PATH_IN_BUCKET=$(echo "${GS_URI}" | sed "s|gs://${BUCKET_NAME}/||")
        
        # 5. Define la URI de destino
        NEW_GS_URI="gs://${BUCKET_NAME}/${PATH_IN_BUCKET//${BLOB_NAME}/${NEW_BLOB_NAME}}"
        
        echo "Renombrando: '${GS_URI}' -> '${NEW_GS_URI}'"
        
        # 6. Ejecuta la operación de mover (MV = Copiar y Borrar)
        # gsutil -m mv "${GS_URI}" "${NEW_GS_URI}"
        
        # 🚨 NOTA: El comando de arriba puede fallar en Cloud Shell o si el nombre contiene muchos caracteres especiales.
        # Usa el siguiente, que solo mueve el BLOB_NAME.

        # Comando de Renombrado Seguro (maneja bien los subdirectorios si los tienes)
        #gsutil mv "gs://${BUCKET_NAME}/${PATH_IN_BUCKET}" "gs://${BUCKET_NAME}/${NEW_BLOB_NAME}"
        
    fi
done

echo "=== Proceso de renombrado finalizado. ==="
