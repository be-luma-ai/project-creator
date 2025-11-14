# Cloud Functions

Este directorio contiene las Cloud Functions del proyecto.

## Funciones Disponibles

### sync-clients-to-gcs

Sincroniza automáticamente los clientes de Firestore a Cloud Storage cuando hay cambios.

**Ubicación**: `sync_clients_to_gcs/`

**Trigger**: Firestore (colección `clients`)

**Función**: Cuando se crea, actualiza o elimina un cliente en Firestore, actualiza `clients.json` en Cloud Storage.

Ver [sync_clients_to_gcs/README.md](./sync_clients_to_gcs/README.md) para más detalles.

## Deploy

Cada función tiene su propio script de deploy. Ver el README específico de cada función.

## Permisos Requeridos

Las Cloud Functions necesitan:
- Acceso a Firestore (lectura)
- Acceso a Cloud Storage (escritura)
- Service account con permisos adecuados

