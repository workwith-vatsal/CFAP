'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  User as UserIcon,
  ArrowLeft,
  KeyRound,
} from 'lucide-react';
import { useAuth } from '@/lib/auth/AuthContext';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { PasswordInput } from '@/components/ui/PasswordInput';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { LanguageSelector } from '@/components/ui/LanguageSelector';
import { PasswordStrengthIndicator } from '@/components/auth/PasswordStrengthIndicator';
import { apiClient } from '@/lib/api/apiClient';
import { MessageResponse } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export default function ProfilePage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const { t } = useLanguage();
  const router = useRouter();

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/auth/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-100">
        <LoadingSpinner size="lg" className="text-indigo-500" />
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(null);

    if (!currentPassword) {
      setPasswordError('Please enter your current password.');
      return;
    }
    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters.');
      return;
    }
    if (newPassword === currentPassword) {
      setPasswordError('New password must be different from current password.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError(t.register.passwordMatchError);
      return;
    }

    setIsChangingPassword(true);

    try {
      const res = await apiClient.post<MessageResponse>(
        '/api/v1/auth/change-password',
        {
          current_password: currentPassword,
          new_password: newPassword,
        }
      );
      setPasswordSuccess(res.message || t.profile.changePasswordSuccess);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Failed to change password. Please check current password.';
      setPasswordError(msg);
    } finally {
      setIsChangingPassword(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Back Link & Header */}
        <div>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-slate-100 mb-4 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>{t.dashboard.overview}</span>
          </Link>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">
                {t.profile.title}
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                {t.profile.subtitle}
              </p>
            </div>
            <LanguageSelector />
          </div>
        </div>

        {/* Personal Information Card */}
        <div className="p-6 sm:p-8 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xs space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <UserIcon className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-100">
                {t.profile.personalInfo}
              </h2>
              <p className="text-xs text-slate-400">
                Your account credentials and verification status
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div className="space-y-1">
              <span className="text-xs font-medium text-slate-400">
                {t.profile.fullName}
              </span>
              <div className="text-sm font-semibold text-slate-100 p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                {user.first_name} {user.last_name}
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-xs font-medium text-slate-400">
                {t.profile.email}
              </span>
              <div className="text-sm font-mono text-slate-100 p-2.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
                <span>{user.email}</span>
                <span className="text-[10px] font-sans px-2 py-0.5 rounded-full bg-emerald-950 border border-emerald-800 text-emerald-300">
                  {user.is_verified ? t.profile.verified : 'Pending'}
                </span>
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-xs font-medium text-slate-400">
                {t.profile.mobile}
              </span>
              <div className="text-sm font-mono text-slate-100 p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                {user.mobile || '— Not provided —'}
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-xs font-medium text-slate-400">
                {t.profile.authProvider}
              </span>
              <div className="text-sm text-slate-100 p-2.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between capitalize">
                <span>{user.auth_provider}</span>
                <span className="text-[10px] font-sans px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                  Role: {user.role}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Security & Change Password Card */}
        <div className="p-6 sm:p-8 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xs space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <div className="w-10 h-10 rounded-xl bg-violet-600/20 border border-violet-500/30 flex items-center justify-center text-violet-400">
              <KeyRound className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-100">
                {t.profile.changePasswordTitle}
              </h2>
              <p className="text-xs text-slate-400">
                Update your account password with cryptographic verification
              </p>
            </div>
          </div>

          {user.auth_provider !== 'local' ? (
            <Alert variant="info">{t.profile.oauthPasswordNotice}</Alert>
          ) : (
            <form onSubmit={handleChangePassword} className="space-y-4 max-w-lg">
              {passwordError && (
                <Alert
                  variant="error"
                  onClose={() => setPasswordError(null)}
                >
                  {passwordError}
                </Alert>
              )}
              {passwordSuccess && (
                <Alert
                  variant="success"
                  onClose={() => setPasswordSuccess(null)}
                >
                  {passwordSuccess}
                </Alert>
              )}

              <PasswordInput
                label={t.profile.currentPasswordLabel}
                required
                placeholder="Current password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />

              <div>
                <PasswordInput
                  label={t.profile.newPasswordLabel}
                  required
                  placeholder="New secure password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
                <PasswordStrengthIndicator password={newPassword} />
              </div>

              <PasswordInput
                label={t.profile.confirmNewPasswordLabel}
                required
                placeholder="Confirm new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />

              <Button
                type="submit"
                variant="primary"
                size="md"
                className="mt-2"
                isLoading={isChangingPassword}
                loadingText={t.profile.updatingPassword}
              >
                {t.profile.changePasswordButton}
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
