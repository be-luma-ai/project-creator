"""
Script para testear la Cloud Function localmente usando Firebase Emulator.

Prerequisitos:
1. Instalar Firebase Tools: npm install -g firebase-tools
2. Inicializar emuladores: firebase init emulators
3. Iniciar emuladores: firebase emulators:start

Uso:
    python test_local.py
"""

import json
import os
import sys

# Configurar para usar emuladores locales ANTES de importar las librerías
os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:9023'
os.environ['GCLOUD_PROJECT'] = 'test-project'

# Importar después de configurar variables de entorno
from google.cloud import firestore
from google.cloud import storage

# Importar la función después de configurar variables de entorno
from main_firestore_trigger import sync_clients_firestore


class MockContext:
    """Mock del contexto de Firestore para testing"""
    def __init__(self, event_type='providers/cloud.firestore/eventTypes/document.write'):
        self.event_type = event_type
        self.resource = 'projects/test-project/databases/(default)/documents/clients/test-client'


def setup_test_data():
    """Configura datos de prueba en Firestore Emulator"""
    print("🔧 Setting up test data in Firestore Emulator...")
    
    db = firestore.Client(project='test-project')
    clients_ref = db.collection('clients')
    
    # Limpiar datos existentes
    docs = clients_ref.stream()
    for doc in docs:
        doc.reference.delete()
    
    # Agregar clientes de prueba
    test_clients = [
        {
            "name": "GAMA S.A",
            "slug": "gama",
            "business_id": "1518026538611779",
            "project_id": "gama-454419",
            "google_ads_customer_id": "123-456-7890",
            "created_at": firestore.SERVER_TIMESTAMP,
            "created_by": "test-user"
        },
        {
            "name": "Bruta Marketing",
            "slug": "bruta",
            "business_id": "197526051543568",
            "project_id": "bruta-123456",
            "created_at": firestore.SERVER_TIMESTAMP,
            "created_by": "test-user"
        }
    ]
    
    for client in test_clients:
        clients_ref.add(client)
    
    print(f"✅ Added {len(test_clients)} test clients to Firestore")


def verify_gcs_output():
    """Verifica que el archivo se haya creado correctamente en Cloud Storage Emulator"""
    print("\n🔍 Verifying output in Cloud Storage Emulator...")
    
    try:
        storage_client = storage.Client(project='test-project')
        bucket = storage_client.bucket('clients-config')
        blob = bucket.blob('clients.json')
        
        if blob.exists():
            content = blob.download_as_text()
            clients = json.loads(content)
            
            print(f"✅ File exists in GCS with {len(clients)} clients")
            print("\n📄 Content:")
            print(json.dumps(clients, indent=2, ensure_ascii=False))
            
            # Validar formato
            assert isinstance(clients, list), "clients.json should be an array"
            assert len(clients) > 0, "clients.json should not be empty"
            
            for client in clients:
                assert "slug" in client, "Each client should have 'slug'"
                assert "business_id" in client, "Each client should have 'business_id'"
            
            print("\n✅ Format validation passed!")
            return True
        else:
            print("❌ File not found in GCS")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying GCS: {e}")
        return False


def test_function():
    """Ejecuta la función de sincronización"""
    print("\n🚀 Testing sync function...")
    
    try:
        # Crear mock context
        context = MockContext()
        
        # Ejecutar función
        result = sync_clients_firestore(None, context)
        
        print(f"✅ Function executed successfully")
        print(f"📊 Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Error executing function: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal de testing"""
    print("=" * 60)
    print("🧪 Testing Cloud Function Locally")
    print("=" * 60)
    
    # Verificar que los emuladores estén corriendo
    print("\n⚠️  Make sure Firebase Emulators are running:")
    print("   firebase emulators:start")
    print()
    
    input("Press Enter when emulators are running...")
    
    # Setup test data
    try:
        setup_test_data()
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        print("\n💡 Make sure Firestore Emulator is running on localhost:8080")
        sys.exit(1)
    
    # Test function
    if not test_function():
        sys.exit(1)
    
    # Verify output
    if not verify_gcs_output():
        print("\n💡 Make sure Storage Emulator is running on localhost:9023")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

