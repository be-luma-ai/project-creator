"""
Script para testear la Cloud Function en producción.

Este script:
1. Crea un cliente de prueba en Firestore (producción)
2. Espera a que el trigger ejecute la función
3. Verifica que clients.json se haya actualizado en Cloud Storage

Prerequisitos:
- gcloud CLI instalado y autenticado: gcloud auth application-default login
- Proyecto configurado: gcloud config set project be-luma-infra

Uso:
    python test_prod.py
"""

import json
import time
import os
from google.cloud import firestore
from google.cloud import storage

# Obtener PROJECT_ID de gcloud config o usar default
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'be-luma-infra')
BUCKET_NAME = "clients-config"
FILE_NAME = "clients.json"

print(f"📦 Using project: {PROJECT_ID}")
print(f"💡 To change project: gcloud config set project YOUR_PROJECT_ID")
print()


def create_test_client():
    """Crea un cliente de prueba en Firestore"""
    print("🔧 Creating test client in Firestore...")
    
    db = firestore.Client(project=PROJECT_ID)
    clients_ref = db.collection('clients')
    
    # Cliente de prueba con timestamp único
    timestamp = int(time.time())
    test_client = {
        "name": f"Test Client {timestamp}",
        "slug": f"test-client-{timestamp}",
        "business_id": f"999999999{timestamp}",
        "project_id": f"test-{timestamp}",
        "created_at": firestore.SERVER_TIMESTAMP,
        "created_by": "test-script"
    }
    
    # Agregar cliente
    doc_ref = clients_ref.add(test_client)
    client_id = doc_ref[1].id
    
    print(f"✅ Created test client: {test_client['slug']} (ID: {client_id})")
    return client_id, test_client['slug']


def get_gcs_file_timestamp():
    """Obtiene el timestamp de última modificación del archivo en GCS"""
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(FILE_NAME)
        
        if blob.exists():
            blob.reload()
            return blob.updated
        return None
    except Exception as e:
        print(f"⚠️  Error getting file timestamp: {e}")
        return None


def verify_gcs_file(expected_slug=None):
    """Verifica que el archivo en GCS contenga el cliente de prueba"""
    print("\n🔍 Verifying clients.json in Cloud Storage...")
    
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(FILE_NAME)
        
        if not blob.exists():
            print("❌ File not found in GCS")
            return False
        
        # Descargar y parsear
        content = blob.download_as_text()
        clients = json.loads(content)
        
        print(f"✅ File exists with {len(clients)} clients")
        
        # Si se especificó un slug, verificar que esté presente
        if expected_slug:
            found = any(c.get("slug") == expected_slug for c in clients)
            if found:
                print(f"✅ Test client '{expected_slug}' found in file")
            else:
                print(f"⚠️  Test client '{expected_slug}' not found yet (may need to wait)")
                return False
        
        # Mostrar contenido
        print("\n📄 Current clients.json content:")
        print(json.dumps(clients, indent=2, ensure_ascii=False))
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying GCS: {e}")
        import traceback
        traceback.print_exc()
        return False


def wait_for_sync(max_wait=30):
    """Espera a que la función se ejecute (máximo max_wait segundos)"""
    print(f"\n⏳ Waiting for Cloud Function to sync (max {max_wait}s)...")
    
    initial_timestamp = get_gcs_file_timestamp()
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        time.sleep(2)
        current_timestamp = get_gcs_file_timestamp()
        
        if current_timestamp and current_timestamp != initial_timestamp:
            elapsed = time.time() - start_time
            print(f"✅ File updated after {elapsed:.1f} seconds")
            return True
        
        print(".", end="", flush=True)
    
    print(f"\n⚠️  Timeout: Function may not have executed within {max_wait}s")
    return False


def cleanup_test_client(client_id):
    """Elimina el cliente de prueba"""
    print(f"\n🧹 Cleaning up test client (ID: {client_id})...")
    
    try:
        db = firestore.Client(project=PROJECT_ID)
        doc_ref = db.collection('clients').document(client_id)
        doc_ref.delete()
        print("✅ Test client deleted")
    except Exception as e:
        print(f"⚠️  Error deleting test client: {e}")


def main():
    """Función principal de testing en producción"""
    print("=" * 60)
    print("🧪 Testing Cloud Function in Production")
    print("=" * 60)
    print(f"📦 Project: {PROJECT_ID}")
    print(f"🪣 Bucket: {BUCKET_NAME}")
    print()
    
    # Confirmar
    response = input("⚠️  This will create a test client in PRODUCTION Firestore. Continue? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Cancelled")
        return
    
    try:
        # Crear cliente de prueba
        client_id, client_slug = create_test_client()
        
        # Esperar a que se sincronice
        if wait_for_sync(max_wait=30):
            # Verificar archivo
            if verify_gcs_file(expected_slug=client_slug):
                print("\n" + "=" * 60)
                print("✅ Test passed! Function is working correctly.")
                print("=" * 60)
            else:
                print("\n" + "=" * 60)
                print("⚠️  File updated but test client not found. Check manually.")
                print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("⚠️  Function may not have executed. Check Cloud Functions logs.")
            print("=" * 60)
            print("\n💡 Check logs with:")
            print("   gcloud functions logs read sync-clients-to-gcs --region=us-central1 --limit=50")
        
        # Limpiar
        cleanup = input("\n🧹 Delete test client? (yes/no): ")
        if cleanup.lower() == "yes":
            cleanup_test_client(client_id)
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

