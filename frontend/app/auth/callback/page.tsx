'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Sparkles } from 'lucide-react';
import { useAuth } from '@/lib/auth/AuthContext';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export default function AuthCallbackPage() {
  const router = useRouter();
  const { refreshUser } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function handleAuth() {
      try {
        const user = await refreshUser();
        if (user && isMounted) {
          router.replace('/dashboard');
        } else if (isMounted) {
          router.replace('/auth/login?error=oauth_failed');
        }
      } catch {
        if (isMounted) {
          setError('Authentication verification failed.');
          setTimeout(() => router.replace('/auth/login?error=oauth_failed'), 2000);
        }
      }
    }

    handleAuth();

    return () => {
      isMounted = false;
    };
  }, [refreshUser, router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 text-slate-100">
      <div className="flex flex-col items-center space-y-4 text-center max-w-sm px-4">
        <div className="w-12 h-12 rounded-xl bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-600/30 animate-pulse">
          <Sparkles className="w-6 h-6 text-white" />
        </div>
        <h2 className="text-base font-semibold text-slate-100">
          Authenticating your session...
        </h2>
        <p className="text-xs text-slate-400">
          Verifying security credentials and preparing your CFAP workspace.
        </p>
        <LoadingSpinner size="md" className="text-indigo-400 mt-2" />
        {error && <p className="text-xs text-red-400 mt-2">{error}</p>}
      </div>
    </div>
  );
}
