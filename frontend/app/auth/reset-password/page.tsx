'use client';

import React, { useState, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { AuthCard } from '@/components/auth/AuthCard';
import { PasswordStrengthIndicator } from '@/components/auth/PasswordStrengthIndicator';
import { Input } from '@/components/ui/Input';
import { PasswordInput } from '@/components/ui/PasswordInput';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { apiClient } from '@/lib/api/apiClient';
import { MessageResponse } from '@/types';
import { isValidEmail } from '@/lib/validation';

function ResetPasswordContent() {
  const { t } = useLanguage();
  const router = useRouter();
  const searchParams = useSearchParams();

  const initialEmail = searchParams.get('email') || '';
  const [email, setEmail] = useState(initialEmail);
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const targetEmail = email.trim() || initialEmail.trim();

    if (!targetEmail || !isValidEmail(targetEmail)) {
      setError('Please provide a valid email address.');
      return;
    }
    if (otp.length !== 6) {
      setError('Please enter the 6-digit reset code.');
      return;
    }
    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError(t.register.passwordMatchError);
      return;
    }

    setIsLoading(true);

    try {
      await apiClient.post<MessageResponse>('/api/v1/auth/reset-password', {
        email: targetEmail.toLowerCase(),
        otp: otp.trim(),
        new_password: newPassword,
      });

      router.push('/auth/login?reset=true');
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Password reset failed. Please check your code.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthCard
      title={t.resetPassword.title}
      subtitle={t.resetPassword.subtitle}
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

        <Input
          label={t.resetPassword.otpLabel}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={6}
          required
          placeholder="123456"
          value={otp}
          onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
        />

        <div>
          <PasswordInput
            label={t.resetPassword.newPasswordLabel}
            required
            placeholder={t.auth.passwordPlaceholder}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          <PasswordStrengthIndicator password={newPassword} />
        </div>

        <PasswordInput
          label={t.resetPassword.confirmNewPasswordLabel}
          required
          placeholder={t.auth.passwordPlaceholder}
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
        />

        <Button
          type="submit"
          variant="primary"
          size="md"
          className="w-full mt-2"
          isLoading={isLoading}
          loadingText={t.resetPassword.submitting}
        >
          {t.resetPassword.submitButton}
        </Button>
      </form>
    </AuthCard>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-100">
          Loading...
        </div>
      }
    >
      <ResetPasswordContent />
    </Suspense>
  );
}
