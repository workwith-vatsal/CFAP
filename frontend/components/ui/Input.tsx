import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export function Input({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  id,
  className = '',
  required,
  ...props
}: InputProps) {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="w-full space-y-1.5">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-xs font-medium text-slate-300 tracking-wide"
        >
          {label} {required && <span className="text-red-400">*</span>}
        </label>
      )}
      <div className="relative rounded-lg shadow-sm">
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            {leftIcon}
          </div>
        )}
        <input
          id={inputId}
          required={required}
          className={`block w-full rounded-lg bg-slate-900 border text-slate-100 placeholder-slate-500 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50 disabled:bg-slate-950 ${
            error
              ? 'border-red-500/80 focus:ring-red-500'
              : 'border-slate-700/80 hover:border-slate-600'
          } ${leftIcon ? 'pl-10' : 'pl-3.5'} ${
            rightIcon ? 'pr-10' : 'pr-3.5'
          } py-2.5 ${className}`}
          {...props}
        />
        {rightIcon && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            {rightIcon}
          </div>
        )}
      </div>
      {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
      {!error && helperText && (
        <p className="text-xs text-slate-400 mt-1">{helperText}</p>
      )}
    </div>
  );
}
