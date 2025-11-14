import { initializeApp, getApps, cert, App } from 'firebase-admin/app';
import { getAuth, Auth } from 'firebase-admin/auth';
import { getFirestore, Firestore } from 'firebase-admin/firestore';

let app: App;
let authAdmin: Auth;
let db: Firestore;

function initializeFirebaseAdmin() {
  if (getApps().length === 0) {
    const projectId = process.env.FIREBASE_PROJECT_ID;
    const clientEmail = process.env.FIREBASE_CLIENT_EMAIL;
    const privateKey = process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n');

    if (!projectId || !clientEmail || !privateKey) {
      throw new Error('Missing Firebase Admin environment variables');
    }

    app = initializeApp({
      credential: cert({
        projectId,
        clientEmail,
        privateKey,
      }),
    });

    authAdmin = getAuth(app);
    db = getFirestore(app);
  } else {
    app = getApps()[0];
    authAdmin = getAuth(app);
    db = getFirestore(app);
  }

  return { app, authAdmin, db };
}

// Singleton pattern - inicializar una sola vez
const { authAdmin: adminAuth, db: adminDb } = initializeFirebaseAdmin();

export { adminAuth, adminDb };

