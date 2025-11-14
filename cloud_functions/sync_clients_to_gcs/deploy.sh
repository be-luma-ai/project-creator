#!/bin/bash

# Script para deploy de la Cloud Function
# Uso: ./deploy.sh

set -e

PROJECT_ID="be-luma-infra"
FUNCTION_NAME="sync-clients-to-gcs"
REGION="us-central1"
RUNTIME="python311"
ENTRY_POINT="sync_clients_firestore"
SERVICE_ACCOUNT="${FUNCTION_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🚀 Deploying Cloud Function: ${FUNCTION_NAME}"

# Deploy con Firestore Trigger
gcloud functions deploy ${FUNCTION_NAME} \
  --gen2 \
  --runtime=${RUNTIME} \
  --region=${REGION} \
  --source=. \
  --entry-point=${ENTRY_POINT} \
  --trigger-event-filters="type=google.cloud.firestore.document.v1.written" \
  --trigger-event-filters="database=(default)" \
  --trigger-resource="projects/${PROJECT_ID}/databases/(default)/documents/clients/{document=**}" \
  --service-account=${SERVICE_ACCOUNT} \
  --project=${PROJECT_ID} \
  --memory=256MB \
  --timeout=60s \
  --max-instances=10

echo "✅ Deploy completed!"
echo ""
echo "📋 Next steps:"
echo "1. Verify the function is running:"
echo "   gcloud functions describe ${FUNCTION_NAME} --region=${REGION} --gen2"
echo ""
echo "2. Check logs:"
echo "   gcloud functions logs read ${FUNCTION_NAME} --region=${REGION} --limit=50"
echo ""
echo "3. Test by creating a client in Firestore and verify clients.json is updated in GCS"

