/**
 * Validaciones centralizadas para el onboarding de clientes
 */

export interface ClientInput {
  name: string;
  slug: string;
  business_id: string;
  google_ads_customer_id?: string;
  project_id: string;
}

export interface ValidationError {
  field: string;
  message: string;
}

/**
 * Valida el formato del nombre
 */
export function validateName(name: string): ValidationError | null {
  if (!name || !name.trim()) {
    return { field: 'name', message: 'El nombre es requerido' };
  }
  if (name.length < 2) {
    return { field: 'name', message: 'El nombre debe tener al menos 2 caracteres' };
  }
  if (name.length > 100) {
    return { field: 'name', message: 'El nombre no puede exceder 100 caracteres' };
  }
  return null;
}

/**
 * Valida el formato del slug
 */
export function validateSlug(slug: string): ValidationError | null {
  if (!slug || !slug.trim()) {
    return { field: 'slug', message: 'El slug es requerido' };
  }
  // GCP project ID format: 6-30 chars, lowercase, numbers, hyphens
  if (!/^[a-z][a-z0-9-]{4,28}[a-z0-9]$/.test(slug)) {
    return {
      field: 'slug',
      message: 'El slug debe tener entre 6-30 caracteres, solo minúsculas, números y guiones',
    };
  }
  return null;
}

/**
 * Valida el Business ID de Meta
 */
export function validateBusinessId(businessId: string): ValidationError | null {
  if (!businessId || !businessId.trim()) {
    return { field: 'business_id', message: 'El Business ID es requerido' };
  }
  if (!/^\d+$/.test(businessId)) {
    return { field: 'business_id', message: 'El Business ID debe contener solo números' };
  }
  if (businessId.length < 10 || businessId.length > 20) {
    return {
      field: 'business_id',
      message: 'El Business ID debe tener entre 10 y 20 dígitos',
    };
  }
  return null;
}

/**
 * Valida el Google Ads Customer ID (opcional)
 */
export function validateGoogleAdsCustomerId(customerId?: string): ValidationError | null {
  if (!customerId) {
    return null; // Es opcional
  }
  if (!/^\d{3}-\d{3}-\d{4}$/.test(customerId)) {
    return {
      field: 'google_ads_customer_id',
      message: 'Formato inválido. Use: XXX-XXX-XXXX',
    };
  }
  return null;
}

/**
 * Valida el Project ID
 */
export function validateProjectId(projectId: string): ValidationError | null {
  if (!projectId || !projectId.trim()) {
    return { field: 'project_id', message: 'El Project ID es requerido' };
  }
  // GCP project ID format
  if (!/^[a-z][a-z0-9-]{4,58}[a-z0-9]$/.test(projectId)) {
    return {
      field: 'project_id',
      message: 'El Project ID debe seguir el formato de GCP (6-60 caracteres)',
    };
  }
  return null;
}

/**
 * Valida todos los campos del cliente
 */
export function validateClientInput(input: ClientInput): ValidationError[] {
  const errors: ValidationError[] = [];

  const nameError = validateName(input.name);
  if (nameError) errors.push(nameError);

  const slugError = validateSlug(input.slug);
  if (slugError) errors.push(slugError);

  const businessIdError = validateBusinessId(input.business_id);
  if (businessIdError) errors.push(businessIdError);

  const googleAdsError = validateGoogleAdsCustomerId(input.google_ads_customer_id);
  if (googleAdsError) errors.push(googleAdsError);

  const projectIdError = validateProjectId(input.project_id);
  if (projectIdError) errors.push(projectIdError);

  return errors;
}

