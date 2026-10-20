'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AuthCard } from '@/components/auth/AuthCard';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { apiClient } from '@/lib/api/apiClient';
import { MessageResponse } from '@/types';
import { isValidEmail } from '@/lib/validation';

export default function ForgotPasswordPage() {
  const { t } = useLanguage();
  const router = useRouter();

  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !isValidEmail(email)) {
      setError('Please provide a valid email address.');
      return;
    }

    setIsLoading(true);

    try {
      await apiClient.post<MessageResponse>('/api/v1/auth/forgot-password', {
        email: email.trim().toLowerCase(),
      });
      setSubmitted(true);
    } catch {
      // Always treat as success to prevent email enumeration
      setSubmitted(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthCard
      title={t.forgotPassword.title}
      subtitle={t.forgotPassword.subtitle}
      footer={
        <p className="text-slate-400">
          <Link
            href="/auth/login"
            className="font-medium text-indigo-400 hover:text-indigo-300 transition-colors focus:outline-none underline"
          >
            {t.auth.backToLogin}
          </Link>
        </p>
      }
    >
      {submitted ? (
        <div className="space-y-5">
          <Alert variant="info">{t.forgotPassword.genericNotice}</Alert>
          <Button
            variant="primary"
            size="md"
            className="w-full"
            onClick={() =>
              router.push(
                `/auth/reset-password?email=${encodeURIComponent(
                  email.trim().toLowerCase()
                )}`
              )
            }
          >
            {t.forgotPassword.proceedToReset}
          </Button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Input
            label={t.auth.emailLabel}
            type="email"
            required
            placeholder={t.auth.emailPlaceholder}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <Button
            type="submit"
            variant="primary"
            size="md"
            className="w-full mt-2"
            isLoading={isLoading}
            loadingText={t.forgotPassword.submitting}
          >
            {t.forgotPassword.submitButton}
          </Button>
        </form>
      )}
    </AuthCard>
  );
}
