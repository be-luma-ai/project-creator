# Arquitectura del Sistema

## Flujo Completo

```
┌─────────────────┐
│  Frontend       │
│  (Vercel)       │
│  - Next.js      │
│  - Firebase Auth│
└────────┬────────┘
         │
         │ 1. Usuario crea cliente
         ▼
┌─────────────────┐
│  Firestore      │
│  (clients)      │
└────────┬────────┘
         │
         │ 2. Firestore Trigger
         ▼
┌─────────────────┐
│  Cloud Function │
│  sync-clients-  │
│  to-gcs         │
└────────┬────────┘
         │
         │ 3. Actualiza JSON
         ▼
┌─────────────────┐
│  Cloud Storage  │
│  clients.json   │
└────────┬────────┘
         │
         │ 4. Pipeline lee JSON
         ▼
┌─────────────────┐
│  Pipeline Python│
│  (Cloud Run)    │
│  - Meta API     │
│  - BigQuery     │
└────────┬────────┘
         │
         │ 5. Escribe datos
         ▼
┌─────────────────┐
│  BigQuery       │
│  (por cliente)  │
└─────────────────┘
```

## Componentes

### 1. Frontend (Vercel)
- **Tecnología**: Next.js + TypeScript
- **Autenticación**: Firebase Auth (Google)
- **Base de datos**: Firestore
- **Función**: Onboarding de clientes

### 2. Firestore
- **Colección**: `clients`
- **Estructura**:
  ```json
  {
    "name": "GAMA S.A",
    "slug": "gama-sa",
    "business_id": "1518026538611779",
    "project_id": "gama-sa-454419",
    "google_ads_customer_id": "123-456-7890",
    "created_at": "2025-10-03T...",
    "created_by": "user-id"
  }
  ```

### 3. Cloud Function (sync-clients-to-gcs)
- **Trigger**: Firestore (colección `clients`)
- **Función**: Sincroniza Firestore → Cloud Storage
- **Output**: `gs://clients-config/clients.json`

### 4. Cloud Storage
- **Bucket**: `clients-config`
- **Archivo**: `clients.json`
- **Formato**: JSON array con clientes

### 5. Pipeline Python (Cloud Run)
- **Trigger**: Cloud Scheduler (diario)
- **Función**: 
  - Lee `clients.json` de Cloud Storage
  - Extrae datos de Meta API
  - Escribe en BigQuery de cada cliente

### 6. BigQuery
- **Proyecto**: Cada cliente tiene su propio proyecto
- **Dataset**: `meta_ads`
- **Tablas**: `{table_name}_{YYYYMMDD}`

## Service Accounts

### Frontend → Firestore
- Usa Firebase Auth (usuarios autenticados)

### Cloud Function → Firestore/Storage
- Service account de Cloud Functions
- Permisos: `datastore.user`, `storage.objectAdmin`

### Pipeline → Meta API
- Token de Meta desde Secret Manager

### Pipeline → BigQuery
- **Opción actual**: Service account por cliente
- **Opción futura**: Una SA central con permisos cross-project

## Sincronización

### Firestore → Cloud Storage
- **Automática**: Firestore Trigger
- **Frecuencia**: Inmediata (cuando hay cambios)
- **Función**: `sync-clients-to-gcs`

### Cloud Storage → Pipeline
- **Manual**: Pipeline lee al ejecutarse
- **Frecuencia**: Diaria (Cloud Scheduler)

## Ventajas de esta Arquitectura

1. **Fuente de verdad única**: Firestore
2. **Sincronización automática**: Sin intervención manual
3. **Compatibilidad**: Pipeline no necesita cambios
4. **Escalable**: Fácil agregar/quitar clientes
5. **Auditable**: Firestore mantiene historial

