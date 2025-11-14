# Testing de Cloud Function

Guía para testear la Cloud Function tanto localmente como en producción.

## Testing Local

### Prerequisitos

1. **Instalar Firebase Tools**:
```bash
npm install -g firebase-tools
```

2. **Inicializar Firebase Emulators** (si no lo has hecho):
```bash
cd cloud_functions/sync_clients_to_gcs
firebase init emulators
# Seleccionar: Firestore, Storage
```

3. **Iniciar Emuladores**:
```bash
firebase emulators:start
```

Esto iniciará:
- Firestore Emulator en `localhost:8080`
- Storage Emulator en `localhost:9023`

### Ejecutar Test Local

```bash
cd cloud_functions/sync_clients_to_gcs
python test_local.py
```

El script:
1. ✅ Configura datos de prueba en Firestore Emulator
2. ✅ Ejecuta la función de sincronización
3. ✅ Verifica que el archivo se haya creado en Storage Emulator
4. ✅ Valida el formato del JSON

### Testing Manual Local

También puedes testear manualmente:

```python
# En Python
from google.cloud import firestore
from google.cloud import storage

# Configurar emuladores
import os
os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:9023'

# Crear cliente en Firestore
db = firestore.Client(project='test-project')
db.collection('clients').add({
    "name": "Test Client",
    "slug": "test",
    "business_id": "1234567890"
})

# Ejecutar función
from main_firestore_trigger import sync_clients_firestore
# ... ejecutar función ...

# Verificar en Storage
storage_client = storage.Client(project='test-project')
bucket = storage_client.bucket('clients-config')
blob = bucket.blob('clients.json')
print(blob.download_as_text())
```

## Testing en Producción

### Opción 1: Script Automatizado

```bash
cd cloud_functions/sync_clients_to_gcs
python test_prod.py
```

El script:
1. ⚠️  Crea un cliente de prueba en Firestore (producción)
2. ⏳ Espera a que el trigger ejecute la función
3. ✅ Verifica que `clients.json` se haya actualizado
4. 🧹 Opcionalmente elimina el cliente de prueba

### Opción 2: Testing Manual

#### 1. Crear cliente en Firestore (producción)

```python
from google.cloud import firestore

db = firestore.Client(project='be-luma-infra')
db.collection('clients').add({
    "name": "Test Client",
    "slug": "test-client",
    "business_id": "1234567890",
    "project_id": "test-123456",
    "created_at": firestore.SERVER_TIMESTAMP,
    "created_by": "test-user"
})
```

#### 2. Verificar logs de Cloud Function

```bash
gcloud functions logs read sync-clients-to-gcs \
  --region=us-central1 \
  --limit=50
```

#### 3. Verificar archivo en Cloud Storage

```bash
# Ver contenido
gsutil cat gs://clients-config/clients.json

# Ver metadata (última modificación)
gsutil stat gs://clients-config/clients.json
```

#### 4. Verificar en Python

```python
from google.cloud import storage
import json

storage_client = storage.Client(project='be-luma-infra')
bucket = storage_client.bucket('clients-config')
blob = bucket.blob('clients.json')
content = blob.download_as_text()
clients = json.loads(content)

print(f"Total clients: {len(clients)}")
print(json.dumps(clients, indent=2))
```

### Opción 3: Testing con HTTP Trigger (si está configurado)

Si deployaste la función con HTTP trigger para testing:

```bash
# Llamar función directamente
curl -X POST \
  https://us-central1-be-luma-infra.cloudfunctions.net/sync-clients-to-gcs \
  -H "Authorization: bearer $(gcloud auth print-access-token)"
```

## Verificación de Resultados

### Formato Esperado

El archivo `clients.json` debe tener este formato:

```json
[
  {
    "slug": "gama",
    "business_id": "1518026538611779",
    "project_id": "gama-454419"
  },
  {
    "slug": "bruta",
    "business_id": "197526051543568",
    "project_id": "bruta-123456"
  }
]
```

### Validaciones

- ✅ El archivo existe en Cloud Storage
- ✅ Es un JSON válido
- ✅ Es un array
- ✅ Cada cliente tiene `slug` y `business_id`
- ✅ El cliente de prueba está presente (si aplica)

## Troubleshooting

### Error: "Emulator not running"
- Verificar que `firebase emulators:start` esté corriendo
- Verificar puertos: Firestore (8080), Storage (9023)

### Error: "Permission denied"
- Verificar permisos de la service account
- Verificar que el bucket `clients-config` exista

### La función no se ejecuta
- Verificar que el trigger esté configurado
- Revisar logs: `gcloud functions logs read ...`
- Verificar que la colección `clients` exista en Firestore

### El archivo no se actualiza
- Verificar logs de la función
- Verificar que la función tenga permisos de escritura en Storage
- Verificar que el bucket exista

## Checklist de Testing

### Local
- [ ] Emuladores corriendo
- [ ] Test script ejecuta sin errores
- [ ] Archivo se crea en Storage Emulator
- [ ] Formato del JSON es correcto

### Producción
- [ ] Cliente de prueba se crea en Firestore
- [ ] Función se ejecuta (ver logs)
- [ ] Archivo se actualiza en Cloud Storage
- [ ] Cliente de prueba aparece en el JSON
- [ ] Limpieza de datos de prueba

