# Configuración de Variables de Entorno

## Opción 1: Usar valores por defecto (ya configurados)

El código ya tiene los valores de Firebase configurados por defecto, así que **no necesitas crear `.env.local`** para desarrollo local.

## Opción 2: Usar variables de entorno (recomendado para producción)

Crea un archivo `.env.local` en la raíz del proyecto `frontend/` con las siguientes variables:

### Firebase Client (Frontend)

```env
ç
```

## Firebase Admin (Backend - API Routes)

**⚠️ IMPORTANTE**: Estas variables SÍ son necesarias para que funcionen las API routes.

```env
FIREBASE_PROJECT_ID=be-luma-infra
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@be-luma-infra.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
```

## Cómo obtener las credenciales de Firebase Admin:

1. Ve a [Firebase Console](https://console.firebase.google.com/project/be-luma-infra/settings/serviceaccounts/adminsdk)
2. Click en "Generate new private key"
3. Descarga el JSON
4. Extrae los valores:
   - `FIREBASE_PROJECT_ID`: Del campo `project_id` del JSON
   - `FIREBASE_CLIENT_EMAIL`: Del campo `client_email` del JSON
   - `FIREBASE_PRIVATE_KEY`: Del campo `private_key` del JSON (mantén las comillas y los `\n`)

## Nota sobre seguridad:

- **Nunca** commitees el archivo `.env.local` (ya está en `.gitignore`)
- En producción (Vercel), configura estas variables en el dashboard de Vercel
- Los valores por defecto del cliente funcionan para desarrollo, pero las API routes necesitan Firebase Admin
