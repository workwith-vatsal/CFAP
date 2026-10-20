import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export function Card({ children, className = '', ...props }: CardProps) {
  return (
    <div
      className={`rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
