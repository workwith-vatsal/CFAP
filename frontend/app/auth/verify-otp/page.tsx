'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { AuthCard } from '@/components/auth/AuthCard';
import { OtpInput } from '@/components/auth/OtpInput';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { apiClient } from '@/lib/api/apiClient';
import { MessageResponse } from '@/types';

function VerifyOtpContent() {
  const { t } = useLanguage();
  const router = useRouter();
  const searchParams = useSearchParams();

  const initialEmail = searchParams.get('email') || '';
  const [email, setEmail] = useState(initialEmail);
  const [otp, setOtp] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [cooldown, setCooldown] = useState(60);

  // Resend cooldown timer
  useEffect(() => {
    if (cooldown <= 0) return;
    const interval = setInterval(() => {
      setCooldown((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [cooldown]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const targetEmail = email.trim() || initialEmail.trim();

    if (!targetEmail) {
      setError('Please provide your email address.');
      return;
    }
    if (otp.length !== 6) {
      setError('Please enter the complete 6-digit verification code.');
      return;
    }

    setIsLoading(true);

    try {
      await apiClient.post('/api/v1/auth/verify-otp', {
        email: targetEmail.toLowerCase(),
        otp,
      });

      // Redirect to login with verified notice
      router.push('/auth/login?verified=true');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : t.verifyOtp.invalidCode;
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    const targetEmail = email.trim() || initialEmail.trim();
    if (cooldown > 0 || !targetEmail) return;

    setIsResending(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const res = await apiClient.post<MessageResponse>('/api/v1/auth/resend-otp', {
        email: targetEmail.toLowerCase(),
      });
      setSuccessMessage(res.message || t.verifyOtp.resendSuccess);
      setCooldown(60);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to resend OTP at this time.';
      setError(msg);
    } finally {
      setIsResending(false);
    }
  };

  return (
    <AuthCard
      title={t.verifyOtp.title}
      subtitle={
        (initialEmail || email)
          ? `${t.verifyOtp.subtitle} ${initialEmail || email}`
          : 'Enter your email and the 6-digit verification code'
      }
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
      <form onSubmit={handleVerify} className="space-y-5">
        {error && (
          <Alert variant="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        {successMessage && (
          <Alert variant="success" onClose={() => setSuccessMessage(null)}>
            {successMessage}
          </Alert>
        )}

        {!initialEmail && (
          <Input
            label={t.auth.emailLabel}
            type="email"
            required
            placeholder={t.auth.emailPlaceholder}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        )}

        <div className="space-y-2">
          <label className="block text-xs font-medium text-slate-300 text-center">
            Enter 6-Digit Verification Code
          </label>
          <OtpInput
            value={otp}
            onChange={setOtp}
            length={6}
            disabled={isLoading}
            error={!!error}
          />
        </div>

        <Button
          type="submit"
          variant="primary"
          size="md"
          className="w-full"
          isLoading={isLoading}
          loadingText={t.verifyOtp.submitting}
          disabled={otp.length !== 6}
        >
          {t.verifyOtp.submitButton}
        </Button>

        <div className="text-center pt-2 text-xs text-slate-400">
          {cooldown > 0 ? (
            <p>
              {t.verifyOtp.resendWait}{' '}
              <span className="font-mono font-semibold text-indigo-400">
                {cooldown}s
              </span>
            </p>
          ) : (
            <button
              type="button"
              onClick={handleResend}
              disabled={isResending || !(email.trim() || initialEmail.trim())}
              className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors cursor-pointer focus:outline-none underline"
            >
              {isResending ? 'Sending...' : t.verifyOtp.resendButton}
            </button>
          )}
        </div>
      </form>
    </AuthCard>
  );
}

export default function VerifyOtpPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-100">
          Loading verification...
        </div>
      }
    >
      <VerifyOtpContent />
    </Suspense>
  );
}
