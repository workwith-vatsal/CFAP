'use client';

import React, { useId } from 'react';

interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: React.ReactNode;
  error?: string;
}

export function Checkbox({ label, error, id, className = '', ...props }: CheckboxProps) {
  const generatedId = useId();
  const checkboxId = id || generatedId;

  return (
    <div className="space-y-1">
      <div className="flex items-start gap-2.5">
        <div className="flex items-center h-5">
          <input
            id={checkboxId}
            type="checkbox"
            className={`w-4 h-4 rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-slate-900 transition-colors cursor-pointer ${className}`}
            {...props}
          />
        </div>
        <label
          htmlFor={checkboxId}
          className="text-xs text-slate-300 select-none cursor-pointer leading-tight"
        >
          {label}
        </label>
      </div>
      {error && <p className="text-xs text-red-400 pl-6.5">{error}</p>}
    </div>
  );
}
