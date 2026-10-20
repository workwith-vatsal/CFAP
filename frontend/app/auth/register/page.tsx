'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AuthCard } from '@/components/auth/AuthCard';
import { PasswordStrengthIndicator } from '@/components/auth/PasswordStrengthIndicator';
import { Input } from '@/components/ui/Input';
import { PasswordInput } from '@/components/ui/PasswordInput';
import { Checkbox } from '@/components/ui/Checkbox';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { apiClient } from '@/lib/api/apiClient';
import { RegisterResponse } from '@/types';
import { isValidEmail } from '@/lib/validation';

export default function RegisterPage() {
  const { t } = useLanguage();
  const router = useRouter();

  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    mobile: '',
    email: '',
    password: '',
    confirmPassword: '',
    termsAccepted: false,
  });

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.firstName.trim()) {
      errors.firstName = 'First name is required.';
    }
    if (!formData.lastName.trim()) {
      errors.lastName = 'Last name is required.';
    }
    if (!formData.email.trim() || !isValidEmail(formData.email)) {
      errors.email = 'Please provide a valid work email address.';
    }
    if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters.';
    }
    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = t.register.passwordMatchError;
    }
    if (!formData.termsAccepted) {
      errors.termsAccepted = t.register.termsRequiredError;
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneralError(null);

    if (!validateForm()) return;

    setIsLoading(true);

    try {
      await apiClient.post<RegisterResponse>('/api/v1/auth/register', {
        first_name: formData.firstName.trim(),
        last_name: formData.lastName.trim(),
        mobile: formData.mobile.trim() || null,
        email: formData.email.trim().toLowerCase(),
        password: formData.password,
        terms_accepted: formData.termsAccepted,
      });

      // Redirect to OTP verification with email query param
      router.push(
        `/auth/verify-otp?email=${encodeURIComponent(formData.email.trim().toLowerCase())}`
      );
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Registration failed. Please try again.';
      setGeneralError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthCard
      title={t.register.title}
      subtitle={t.register.subtitle}
      footer={
        <p className="text-slate-400">
          {t.auth.alreadyHaveAccount}{' '}
          <Link
            href="/auth/login"
            className="font-medium text-indigo-400 hover:text-indigo-300 transition-colors focus:outline-none underline"
          >
            {t.nav.signIn}
          </Link>
        </p>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {generalError && (
          <Alert variant="error" onClose={() => setGeneralError(null)}>
            {generalError}
          </Alert>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Input
            label={t.auth.firstNameLabel}
            required
            placeholder="Jane"
            value={formData.firstName}
            error={fieldErrors.firstName}
            onChange={(e) =>
              setFormData({ ...formData, firstName: e.target.value })
            }
          />
          <Input
            label={t.auth.lastNameLabel}
            required
            placeholder="Doe"
            value={formData.lastName}
            error={fieldErrors.lastName}
            onChange={(e) =>
              setFormData({ ...formData, lastName: e.target.value })
            }
          />
        </div>

        <Input
          label={t.auth.emailLabel}
          type="email"
          required
          placeholder={t.auth.emailPlaceholder}
          value={formData.email}
          error={fieldErrors.email}
          onChange={(e) =>
            setFormData({ ...formData, email: e.target.value })
          }
        />

        <Input
          label={t.auth.mobileLabel}
          type="tel"
          placeholder="+1 (555) 000-0000"
          value={formData.mobile}
          error={fieldErrors.mobile}
          onChange={(e) =>
            setFormData({ ...formData, mobile: e.target.value })
          }
        />

        <div>
          <PasswordInput
            label={t.auth.passwordLabel}
            required
            placeholder={t.auth.passwordPlaceholder}
            value={formData.password}
            error={fieldErrors.password}
            onChange={(e) =>
              setFormData({ ...formData, password: e.target.value })
            }
          />
          <PasswordStrengthIndicator password={formData.password} />
        </div>

        <PasswordInput
          label={t.auth.confirmPasswordLabel}
          required
          placeholder={t.auth.passwordPlaceholder}
          value={formData.confirmPassword}
          error={fieldErrors.confirmPassword}
          onChange={(e) =>
            setFormData({ ...formData, confirmPassword: e.target.value })
          }
        />

        <Checkbox
          label={t.auth.termsAgree}
          checked={formData.termsAccepted}
          error={fieldErrors.termsAccepted}
          onChange={(e) =>
            setFormData({ ...formData, termsAccepted: e.target.checked })
          }
        />

        <Button
          type="submit"
          variant="primary"
          size="md"
          className="w-full mt-2"
          isLoading={isLoading}
          loadingText={t.register.submitting}
        >
          {t.register.submitButton}
        </Button>
      </form>
    </AuthCard>
  );
}
