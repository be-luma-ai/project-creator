'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { normalizeNameToSlug, generateProjectId } from '@/lib/utils';

interface ClientData {
  name: string;
  slug: string;
  business_id: string;
  google_ads_customer_id?: string;
  project_id: string;
}

export default function OnboardingForm() {
  const { getIdToken } = useAuth();
  const [formData, setFormData] = useState<ClientData>({
    name: '',
    slug: '',
    business_id: '',
    google_ads_customer_id: '',
    project_id: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  // Generar slug automáticamente cuando cambia el nombre
  useEffect(() => {
    if (formData.name) {
      const slug = normalizeNameToSlug(formData.name);
      const projectId = generateProjectId(slug);
      setFormData(prev => ({
        ...prev,
        slug,
        project_id: projectId,
      }));
    }
  }, [formData.name]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Limpiar error del campo
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'El nombre es requerido';
    }

    if (!formData.slug.trim()) {
      newErrors.slug = 'El slug es requerido';
    } else if (formData.slug.length < 6 || formData.slug.length > 30) {
      newErrors.slug = 'El slug debe tener entre 6 y 30 caracteres';
    }

    if (!formData.business_id.trim()) {
      newErrors.business_id = 'El Business ID es requerido';
    } else if (!/^\d+$/.test(formData.business_id)) {
      newErrors.business_id = 'El Business ID debe contener solo números';
    }

    if (formData.google_ads_customer_id && !/^\d{3}-\d{3}-\d{4}$/.test(formData.google_ads_customer_id)) {
      newErrors.google_ads_customer_id = 'Formato inválido. Use: XXX-XXX-XXXX';
    }

    if (!formData.project_id.trim()) {
      newErrors.project_id = 'El Project ID es requerido';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setLoading(true);
    setSuccess(false);

    try {
      // Obtener token de Firebase Auth
      const token = await getIdToken();
      
      if (!token) {
        throw new Error('No se pudo obtener el token de autenticación');
      }

      const response = await fetch('/api/onboard-client', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token,
          name: formData.name.trim(),
          slug: formData.slug.trim(),
          business_id: formData.business_id.trim(),
          google_ads_customer_id: formData.google_ads_customer_id?.trim() || undefined,
          project_id: formData.project_id.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Error al crear cliente');
      }

      setSuccess(true);
      setErrors({});
      setFormData({
        name: '',
        slug: '',
        business_id: '',
        google_ads_customer_id: '',
        project_id: '',
      });

      setTimeout(() => setSuccess(false), 5000);
    } catch (error: any) {
      console.error('Error creating client:', error);
      setErrors({ submit: error.message || 'Error al crear cliente' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">Onboarding de Cliente</h2>

      {success && (
        <div className="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded">
          ✅ Cliente creado exitosamente
        </div>
      )}

      {errors.submit && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
          {errors.submit}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Nombre del Cliente *
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Ej: GAMA S.A"
            required
          />
          {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
        </div>

        <div>
          <label htmlFor="slug" className="block text-sm font-medium text-gray-700 mb-1">
            Slug (generado automáticamente) *
          </label>
          <input
            type="text"
            id="slug"
            name="slug"
            value={formData.slug}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50"
            readOnly
          />
          <p className="mt-1 text-xs text-gray-500">Este slug se genera automáticamente desde el nombre</p>
        </div>

        <div>
          <label htmlFor="business_id" className="block text-sm font-medium text-gray-700 mb-1">
            Business ID (Meta) *
          </label>
          <input
            type="text"
            id="business_id"
            name="business_id"
            value={formData.business_id}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Ej: 1518026538611779"
            required
          />
          {errors.business_id && <p className="mt-1 text-sm text-red-600">{errors.business_id}</p>}
        </div>

        <div>
          <label htmlFor="google_ads_customer_id" className="block text-sm font-medium text-gray-700 mb-1">
            Google Ads Customer ID (opcional)
          </label>
          <input
            type="text"
            id="google_ads_customer_id"
            name="google_ads_customer_id"
            value={formData.google_ads_customer_id}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Ej: 123-456-7890"
          />
          {errors.google_ads_customer_id && (
            <p className="mt-1 text-sm text-red-600">{errors.google_ads_customer_id}</p>
          )}
        </div>

        <div>
          <label htmlFor="project_id" className="block text-sm font-medium text-gray-700 mb-1">
            Project ID (generado automáticamente) *
          </label>
          <input
            type="text"
            id="project_id"
            name="project_id"
            value={formData.project_id}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50"
            readOnly
          />
          <p className="mt-1 text-xs text-gray-500">Este ID se genera automáticamente para el proyecto GCP</p>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-4 rounded-lg transition"
        >
          {loading ? 'Creando cliente...' : 'Crear Cliente'}
        </button>
      </form>
    </div>
  );
}

