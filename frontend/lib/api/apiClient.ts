const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiRequestError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
    this.data = data;
  }
}

function parseErrorMessage(data: unknown): string {
  if (!data || typeof data !== 'object') return 'An unexpected error occurred.';
  const record = data as Record<string, unknown>;
  if (typeof record.detail === 'string') return record.detail;
  if (Array.isArray(record.detail)) {
    return record.detail
      .map((err: unknown) => {
        if (typeof err === 'object' && err !== null && 'msg' in err) {
          return String((err as { msg: unknown }).msg);
        }
        return JSON.stringify(err);
      })
      .join(', ');
  }
  if (typeof record.message === 'string') return record.message;
  return 'Request failed. Please try again.';
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const config: RequestInit = {
    ...options,
    headers,
    credentials: 'include', // Always send and receive HttpOnly cookies
  };

  try {
    const response = await fetch(url, config);

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    const data: unknown = await response.json().catch(() => null);

    if (!response.ok) {
      const message = parseErrorMessage(data);
      throw new ApiRequestError(message, response.status, data);
    }

    return data as T;
  } catch (error: unknown) {
    if (error instanceof ApiRequestError) {
      throw error;
    }
    throw new ApiRequestError(
      'Unable to connect to CFAP server. Please check your network.',
      0,
      null
    );
  }
}

export const apiClient = {
  get: <T>(endpoint: string, options?: RequestInit) =>
    request<T>(endpoint, { ...options, method: 'GET' }),
  post: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  put: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  patch: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  delete: <T>(endpoint: string, options?: RequestInit) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),
};
