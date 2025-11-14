import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Middleware para validaciones básicas y seguridad
 */
export function middleware(request: NextRequest) {
  // Headers de seguridad
  const response = NextResponse.next();
  
  // Prevenir clickjacking
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');

  return response;
}

export const config = {
  matcher: '/:path*',
};

