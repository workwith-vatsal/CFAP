export interface PasswordStrength {
  score: number; // 0 to 4
  hasMinLength: boolean;
  hasLower: boolean;
  hasUpper: boolean;
  hasNumber: boolean;
  hasSpecial: boolean;
  feedback: string;
}

export function checkPasswordStrength(password: string): PasswordStrength {
  const hasMinLength = password.length >= 8;
  const hasLower = /[a-z]/.test(password);
  const hasUpper = /[A-Z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSpecial = /[^A-Za-z0-9]/.test(password);

  let score = 0;
  if (hasMinLength) score += 1;
  if (hasLower && hasUpper) score += 1;
  if (hasNumber) score += 1;
  if (hasSpecial) score += 1;

  let feedback = 'Weak';
  if (score === 2) feedback = 'Fair';
  if (score === 3) feedback = 'Good';
  if (score === 4) feedback = 'Strong';

  return {
    score,
    hasMinLength,
    hasLower,
    hasUpper,
    hasNumber,
    hasSpecial,
    feedback,
  };
}

export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email.trim());
}
