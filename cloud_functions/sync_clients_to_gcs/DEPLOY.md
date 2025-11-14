# Deploy de Cloud Function - Sync Clients to GCS

Esta Cloud Function sincroniza automáticamente los clientes de Firestore a Cloud Storage cuando hay cambios.

## Prerequisitos

1. **Bucket de Cloud Storage**: `clients-config` debe existir
2. **Firestore**: Colección `clients` debe existir
3. **Permisos**: La service account de Cloud Functions necesita:
   - `roles/datastore.user` (para leer Firestore)
   - `roles/storage.objectAdmin` (para escribir en Cloud Storage)

## Deploy con gcloud CLI

### Opción 1: Deploy con Firestore Trigger (Recomendado)

```bash
gcloud functions deploy sync-clients-to-gcs \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=sync_clients_firestore \
  --trigger-event-filters="type=google.cloud.firestore.document.v1.written" \
  --trigger-event-filters="database=(default)" \
  --trigger-resource="projects/be-luma-infra/databases/(default)/documents/clients/{document=**}" \
  --service-account=YOUR_SERVICE_ACCOUNT@be-luma-infra.iam.gserviceaccount.com \
  --project=be-luma-infra
```

### Opción 2: Deploy con HTTP Trigger (para testing manual)

```bash
gcloud functions deploy sync-clients-to-gcs \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=sync_clients_firestore \
  --trigger-http \
  --allow-unauthenticated \
  --service-account=YOUR_SERVICE_ACCOUNT@be-luma-infra.iam.gserviceaccount.com \
  --project=be-luma-infra
```

## Verificar Deploy

1. **Ver logs**:
```bash
gcloud functions logs read sync-clients-to-gcs --region=us-central1 --limit=50
```

2. **Probar manualmente** (si usas HTTP trigger):
```bash
curl https://REGION-be-luma-infra.cloudfunctions.net/sync-clients-to-gcs
```

3. **Verificar archivo en GCS**:
```bash
gsutil cat gs://clients-config/clients.json
```

## Testing Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar función localmente (requiere emulador de Firestore)
python -m functions_framework --target=sync_clients_firestore --debug
```

## Configuración del Trigger

El trigger se configura automáticamente cuando haces deploy con `--trigger-event-filters`.

**Eventos que disparan la función**:
- `google.cloud.firestore.document.v1.written` - Cuando se crea o actualiza un documento
- `google.cloud.firestore.document.v1.deleted` - Cuando se elimina un documento (opcional)

**Ruta del recurso**:
- `projects/be-luma-infra/databases/(default)/documents/clients/{document=**}`

Esto significa que cualquier cambio en la colección `clients` disparará la función.

## Troubleshooting

### Error: Permission denied
- Verificar que la service account tenga los roles necesarios
- Verificar que el bucket `clients-config` exista y tenga permisos

### Error: Collection not found
- Verificar que la colección `clients` exista en Firestore
- Verificar que el proyecto sea correcto

### La función no se dispara
- Verificar que el trigger esté configurado correctamente
- Revisar logs de Cloud Functions
- Verificar que los eventos de Firestore estén habilitados

