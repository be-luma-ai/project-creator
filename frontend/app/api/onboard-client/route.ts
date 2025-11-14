import { NextRequest, NextResponse } from 'next/server';
import { adminAuth } from '@/lib/firebase-admin';
import { createClient, ClientInput } from '@/services/clientService';

/**
 * API Route para crear un nuevo cliente
 * POST /api/onboard-client
 */
export async function POST(request: NextRequest) {
  try {
    // Obtener token del body o header
    const body = await request.json();
    const token = body.token || request.headers.get('authorization')?.replace('Bearer ', '');

    if (!token) {
      return NextResponse.json({ message: 'No autorizado' }, { status: 401 });
    }

    // Verificar token
    let decodedToken;
    try {
      decodedToken = await adminAuth.verifyIdToken(token);
    } catch (error: any) {
      console.error('Token verification failed:', error);
      return NextResponse.json({ message: 'Token inválido o expirado' }, { status: 401 });
    }

    // Extraer datos del cliente
    const clientInput: ClientInput = {
      name: body.name,
      slug: body.slug,
      business_id: body.business_id,
      google_ads_customer_id: body.google_ads_customer_id,
      project_id: body.project_id,
    };

    // Crear cliente usando el servicio
    const client = await createClient(clientInput, decodedToken.uid);

    return NextResponse.json(
      {
        message: 'Cliente creado exitosamente',
        client: {
          id: client.id,
          name: client.name,
          slug: client.slug,
          project_id: client.project_id,
        },
      },
      { status: 201 }
    );
  } catch (error: any) {
    console.error('Error in onboard-client API:', error);

    // Manejar errores conocidos
    if (error.message.includes('Errores de validación') || error.message.includes('slug ya existe')) {
      return NextResponse.json({ message: error.message }, { status: 400 });
    }

    // Error genérico
    return NextResponse.json(
      { message: error.message || 'Error interno del servidor' },
      { status: 500 }
    );
  }
}

