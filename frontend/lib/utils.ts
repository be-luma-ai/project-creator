/**
 * Normaliza un nombre de empresa a un slug válido
 * Ejemplo: "GAMA S.A" → "gama-sa"
 */
export function normalizeNameToSlug(name: string): string {
  // Normalizar unicode (quitar acentos)
  let slug = name.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  
  // Minúsculas
  slug = slug.toLowerCase();
  
  // Quitar caracteres especiales, dejar solo alfanuméricos y espacios
  slug = slug.replace(/[^\w\s-]/g, '');
  
  // Reemplazar espacios y guiones múltiples por un solo guión
  slug = slug.replace(/[-\s]+/g, '-');
  
  // Quitar guiones al inicio/final
  slug = slug.trim().replace(/^-+|-+$/g, '');
  
  // Validar formato GCP (máx 30 chars, solo minúsculas, números, guiones)
  if (slug.length > 30) {
    slug = slug.substring(0, 30).replace(/-+$/, '');
  }
  
  // Si está vacío, usar "client"
  if (!slug) {
    slug = 'client';
  }
  
  return slug;
}

/**
 * Genera un project_id único
 * Formato: {slug}-{6 dígitos aleatorios}
 */
export function generateProjectId(slug: string): string {
  const random = Math.floor(100000 + Math.random() * 900000); // 6 dígitos
  return `${slug}-${random}`;
}

/**
 * Valida formato de Business ID (solo números)
 */
export function validateBusinessId(businessId: string): boolean {
  return /^\d+$/.test(businessId);
}

/**
 * Valida formato de Google Ads Customer ID (formato: XXX-XXX-XXXX)
 */
export function validateGoogleAdsCustomerId(customerId: string): boolean {
  return /^\d{3}-\d{3}-\d{4}$/.test(customerId);
}

