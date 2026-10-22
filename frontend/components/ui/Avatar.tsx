import React from 'react';

interface AvatarProps {
  name?: string;
  src?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Avatar({
  name = 'User',
  src,
  size = 'md',
  className = '',
}: AvatarProps) {
  const initials = name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();

  const sizeStyles = {
    sm: 'w-7 h-7 text-[10px]',
    md: 'w-8 h-8 text-xs',
    lg: 'w-10 h-10 text-sm font-semibold',
  };

  if (src) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={src}
        alt={name}
        className={`${sizeStyles[size]} rounded-full object-cover border border-slate-700 ${className}`}
      />
    );
  }

  return (
    <div
      className={`${sizeStyles[size]} rounded-full bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 font-medium flex items-center justify-center select-none ${className}`}
    >
      {initials || 'U'}
    </div>
  );
}
