'use client';

import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { Input } from './Input';

interface PasswordInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  error?: string;
  helperText?: string;
}

export function PasswordInput({
  label,
  error,
  helperText,
  ...props
}: PasswordInputProps) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <Input
      type={showPassword ? 'text' : 'password'}
      label={label}
      error={error}
      helperText={helperText}
      rightIcon={
        <button
          type="button"
          onClick={() => setShowPassword((prev) => !prev)}
          className="text-slate-400 hover:text-slate-200 focus:outline-none focus:text-slate-100 p-1 rounded transition-colors"
          tabIndex={-1}
          aria-label={showPassword ? 'Hide password' : 'Show password'}
        >
          {showPassword ? (
            <EyeOff className="w-4 h-4" />
          ) : (
            <Eye className="w-4 h-4" />
          )}
        </button>
      }
      {...props}
    />
  );
}
