# Sync Clients to GCS - Cloud Function

Cloud Function que sincroniza automáticamente los clientes de Firestore a Cloud Storage.

## ¿Qué hace?

Cuando se crea, actualiza o elimina un cliente en Firestore, esta función:
1. Lee todos los clientes de Firestore
2. Convierte el formato al JSON esperado por el pipeline Python
3. Actualiza `clients.json` en Cloud Storage (`gs://clients-config/clients.json`)

## Flujo

```
Frontend (Vercel)
    ↓
Crea cliente en Firestore
    ↓
Firestore Trigger
    ↓
Cloud Function (esta función)
    ↓
Actualiza clients.json en Cloud Storage
    ↓
Pipeline Python lee clients.json
```

## Formato del JSON

El JSON generado tiene el formato esperado por el pipeline:

```json
[
  {
    "slug": "gama",
    "business_id": "1518026538611779",
    "project_id": "gama-454419",
    "google_ads_customer_id": "123-456-7890"
  }
]
```

## Configuración

- **Bucket**: `clients-config`
- **Archivo**: `clients.json`
- **Proyecto**: `be-luma-infra`
- **Colección Firestore**: `clients`

## Deploy

Ver `DEPLOY.md` para instrucciones detalladas.

