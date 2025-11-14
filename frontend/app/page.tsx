'use client';

import { useAuth } from '@/hooks/useAuth';
import Login from '@/components/Login';
import OnboardingForm from '@/components/OnboardingForm';

export default function Home() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Cargando...</div>
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Login />
      <div className="py-8">
        <OnboardingForm />
      </div>
    </div>
  );
}

