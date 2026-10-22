'use client';

import React from 'react';
import { checkPasswordStrength } from '@/lib/validation';

export function PasswordStrengthIndicator({ password }: { password: string }) {
  if (!password) return null;

  const { score, feedback, hasMinLength, hasLower, hasUpper, hasNumber, hasSpecial } =
    checkPasswordStrength(password);

  const getScoreColor = () => {
    if (score <= 1) return 'bg-red-500';
    if (score === 2) return 'bg-amber-500';
    if (score === 3) return 'bg-cyan-500';
    return 'bg-emerald-500';
  };

  const getTextColor = () => {
    if (score <= 1) return 'text-red-400';
    if (score === 2) return 'text-amber-400';
    if (score === 3) return 'text-cyan-400';
    return 'text-emerald-400';
  };

  return (
    <div className="space-y-1.5 mt-2">
      <div className="flex items-center justify-between text-[11px]">
        <span className="text-slate-400">Password strength:</span>
        <span className={`font-semibold ${getTextColor()}`}>{feedback}</span>
      </div>
      <div className="grid grid-cols-4 gap-1.5 h-1">
        {[1, 2, 3, 4].map((step) => (
          <div
            key={step}
            className={`rounded-full transition-colors duration-300 ${
              score >= step ? getScoreColor() : 'bg-slate-800'
            }`}
          />
        ))}
      </div>
      <div className="grid grid-cols-2 gap-x-2 gap-y-0.5 text-[10px] text-slate-400 pt-1">
        <span className={hasMinLength ? 'text-emerald-400' : 'text-slate-500'}>
          {hasMinLength ? '✓' : '•'} 8+ characters
        </span>
        <span className={hasLower && hasUpper ? 'text-emerald-400' : 'text-slate-500'}>
          {hasLower && hasUpper ? '✓' : '•'} Upper & lower case
        </span>
        <span className={hasNumber ? 'text-emerald-400' : 'text-slate-500'}>
          {hasNumber ? '✓' : '•'} Numbers
        </span>
        <span className={hasSpecial ? 'text-emerald-400' : 'text-slate-500'}>
          {hasSpecial ? '✓' : '•'} Special symbols
        </span>
      </div>
    </div>
  );
}
