"""
Versión específica para Firestore Trigger usando functions-framework.
Esta es la función que se debe desplegar como Cloud Function con Firestore trigger.
"""

import json
import logging
from google.cloud import firestore
from google.cloud import storage

# Configuración
BUCKET_NAME = "clients-config"
FILE_NAME = "clients.json"
PROJECT_ID = "be-luma-infra"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def sync_clients_firestore(data, context):
    """
    Cloud Function que se ejecuta cuando hay cambios en la colección 'clients' de Firestore.
    
    Esta función se configura como Firestore Trigger en Cloud Functions.
    
    Args:
        data: Datos del evento de Firestore (puede ser None para algunos eventos)
        context: Contexto del evento (resource, eventType, etc.)
    """
    try:
        # Log del evento
        event_type = getattr(context, 'event_type', 'unknown')
        resource = getattr(context, 'resource', 'unknown')
        
        logger.info(f"🔄 Firestore event: {event_type}")
        logger.info(f"📄 Resource: {resource}")
        
        # Inicializar clientes
        db = firestore.Client(project=PROJECT_ID)
        storage_client = storage.Client(project=PROJECT_ID)
        
        # Leer todos los clientes de Firestore
        clients_ref = db.collection('clients')
        clients_snapshot = clients_ref.stream()
        
        # Convertir a formato JSON esperado por el pipeline
        clients_list = []
        for doc in clients_snapshot:
            client_data = doc.to_dict()
            
            # Formato esperado por el pipeline Python
            client_json = {
                "slug": client_data.get("slug", ""),
                "business_id": client_data.get("business_id", ""),
            }
            
            # Agregar project_id si existe
            if "project_id" in client_data:
                client_json["project_id"] = client_data["project_id"]
            
            # Agregar google_ads_customer_id si existe
            if client_data.get("google_ads_customer_id"):
                client_json["google_ads_customer_id"] = client_data["google_ads_customer_id"]
            
            clients_list.append(client_json)
        
        logger.info(f"📊 Found {len(clients_list)} clients in Firestore")
        
        # Subir a Cloud Storage
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(FILE_NAME)
        
        # Convertir a JSON string
        json_content = json.dumps(clients_list, indent=2, ensure_ascii=False)
        
        # Subir archivo
        blob.upload_from_string(
            json_content,
            content_type='application/json'
        )
        
        logger.info(f"✅ Successfully synced {len(clients_list)} clients to gs://{BUCKET_NAME}/{FILE_NAME}")
        
        result = {
            "status": "success",
            "clients_count": len(clients_list),
            "event_type": str(event_type)
        }
        
        logger.info(f"✅ Sync completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error syncing clients to GCS: {e}", exc_info=True)
        raise

