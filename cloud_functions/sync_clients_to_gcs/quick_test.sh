#!/bin/bash

# Quick test script - Testing local vs production

set -e

echo "🧪 Cloud Function Testing"
echo "=========================="
echo ""
echo "Select testing mode:"
echo "1) Local (with Firebase Emulators)"
echo "2) Production"
echo ""
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "🔧 Starting local test..."
        echo ""
        echo "⚠️  Make sure Firebase Emulators are running:"
        echo "   firebase emulators:start"
        echo ""
        read -p "Press Enter when emulators are running..."
        
        python test_local.py
        ;;
    2)
        echo ""
        echo "🚀 Starting production test..."
        echo ""
        python test_prod.py
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

