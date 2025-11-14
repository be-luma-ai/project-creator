#!/bin/bash

# Script para configurar el entorno de testing

set -e

echo "🔧 Setting up testing environment..."
echo ""

# Verificar gcloud CLI
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first."
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Verificar Firebase Tools
if ! command -v firebase &> /dev/null; then
    echo "⚠️  Firebase Tools not found. Installing..."
    npm install -g firebase-tools
fi

# Configurar credenciales de aplicación default
echo "🔐 Setting up application default credentials..."
gcloud auth application-default login

# Obtener proyecto actual
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")

if [ -z "$CURRENT_PROJECT" ]; then
    echo "⚠️  No project set. Setting to be-luma-infra..."
    gcloud config set project be-luma-infra
    CURRENT_PROJECT="be-luma-infra"
fi

echo "✅ Current project: $CURRENT_PROJECT"
echo ""

# Verificar si Firebase está inicializado
if [ ! -f "firebase.json" ]; then
    echo "⚠️  Firebase not initialized. Initializing..."
    firebase init emulators --project $CURRENT_PROJECT
else
    echo "✅ Firebase already initialized"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Start emulators: firebase emulators:start"
echo "2. Run local test: python test_local.py"
echo "3. Run production test: python test_prod.py"

