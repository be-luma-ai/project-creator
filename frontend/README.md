# Meta Ads Onboarding Frontend

Frontend básico para onboarding de clientes usando Next.js, Firebase Auth y Firestore.

## Setup

1. Instalar dependencias:
```bash
npm install
```

2. Configurar variables de entorno:
```bash
cp .env.local.example .env.local
```

Editar `.env.local` con tus credenciales de Firebase:
- `NEXT_PUBLIC_FIREBASE_API_KEY`
- `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`
- `NEXT_PUBLIC_FIREBASE_PROJECT_ID`
- `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET`
- `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID`
- `NEXT_PUBLIC_FIREBASE_APP_ID`

Para Firebase Admin (API route):
- `FIREBASE_PROJECT_ID`
- `FIREBASE_CLIENT_EMAIL`
- `FIREBASE_PRIVATE_KEY`

3. Ejecutar en desarrollo:
```bash
npm run dev
```

## Estructura

- `app/` - Next.js App Router
- `components/` - Componentes React
- `lib/` - Utilidades y configuración de Firebase
- `app/api/` - API routes

## Funcionalidades

- ✅ Login con Google (Firebase Auth)
- ✅ Formulario de onboarding
- ✅ Generación automática de slug desde nombre
- ✅ Generación automática de project_id
- ✅ Validación de campos
- ✅ Guardado en Firestore

## Deploy en Vercel

1. Conectar repositorio a Vercel
2. Configurar variables de entorno en Vercel
3. Deploy automático

