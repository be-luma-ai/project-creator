/**
 * Servicio para operaciones con clientes en Firestore
 */

import { adminDb } from '@/lib/firebase-admin';
import { validateClientInput, ClientInput, ValidationError } from '@/lib/validations';

export interface Client extends ClientInput {
  id: string;
  created_at: Date;
  created_by: string;
}

/**
 * Verifica si un slug ya existe
 */
export async function slugExists(slug: string): Promise<boolean> {
  try {
    const clientsRef = adminDb.collection('clients');
    const snapshot = await clientsRef.where('slug', '==', slug).limit(1).get();
    return !snapshot.empty;
  } catch (error) {
    console.error('Error checking slug existence:', error);
    throw new Error('Error al verificar disponibilidad del slug');
  }
}

/**
 * Crea un nuevo cliente
 */
export async function createClient(
  input: ClientInput,
  createdBy: string
): Promise<Client> {
  // Validar input
  const validationErrors = validateClientInput(input);
  if (validationErrors.length > 0) {
    const errorMessages = validationErrors.map(e => `${e.field}: ${e.message}`).join(', ');
    throw new Error(`Errores de validación: ${errorMessages}`);
  }

  // Verificar unicidad del slug
  const exists = await slugExists(input.slug);
  if (exists) {
    throw new Error('El slug ya existe. Por favor, use otro nombre.');
  }

  // Crear documento
  const clientData = {
    name: input.name.trim(),
    slug: input.slug.trim(),
    business_id: input.business_id.trim(),
    project_id: input.project_id.trim(),
    google_ads_customer_id: input.google_ads_customer_id?.trim() || null,
    created_at: new Date(),
    created_by: createdBy,
  };

  try {
    const docRef = await adminDb.collection('clients').add(clientData);
    return {
      id: docRef.id,
      ...clientData,
    };
  } catch (error: any) {
    console.error('Error creating client:', error);
    throw new Error('Error al crear cliente en la base de datos');
  }
}

/**
 * Obtiene todos los clientes
 */
export async function getAllClients(): Promise<Client[]> {
  try {
    const snapshot = await adminDb.collection('clients').orderBy('created_at', 'desc').get();
    return snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      created_at: doc.data().created_at.toDate(),
    })) as Client[];
  } catch (error) {
    console.error('Error fetching clients:', error);
    throw new Error('Error al obtener clientes');
  }
}

