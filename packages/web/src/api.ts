/**
 * Minimal bearer-token client for the AJO.ng API.
 *
 * The access token lives in localStorage. That is the pragmatic choice for a
 * demo device (and this is a demo surface), with the caveat stated where it
 * matters: a production web client would use the refresh + access split over
 * HttpOnly cookies. The API already supports both paths; which one the web app
 * uses is a deployment decision, not an API one.
 */
import type {
  AcceptInvitationResult,
  AjoDetail,
  AjoFrequency,
  AjoSummary,
  CollectionDay,
  CreateAjoResult,
  EnrollmentOpenResult,
  InvitationPreview,
  InvitationSummary,
  MeResponse,
} from './api-types';

export class ApiError extends Error {
  readonly status: number;
  readonly code: string | null;

  constructor(status: number, message: string, code: string | null = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

const TOKEN_KEY = 'ajo.web.accessToken';

export function getToken(): string | null {
  return typeof window === 'undefined' ? null : window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token === null) {
    window.localStorage.removeItem(TOKEN_KEY);
  } else {
    window.localStorage.setItem(TOKEN_KEY, token);
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  token?: string | null;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, token = getToken() } = options;
  const headers: Record<string, string> = {};
  if (body !== undefined) {
    headers['content-type'] = 'application/json';
  }
  if (token) {
    headers['authorization'] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, 'The server is unreachable. Is the API running?');
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  let payload: unknown = null;
  if (text.length > 0) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    const message =
      payload && typeof payload === 'object' && 'message' in payload
        ? String((payload as { message: unknown }).message)
        : `Request failed (${response.status}).`;
    const code =
      payload && typeof payload === 'object' && 'error' in payload
        ? String((payload as { error: unknown }).error)
        : null;
    throw new ApiError(response.status, message, code);
  }

  return payload as T;
}

export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
}

export interface RegisterResponse {
  userId: string;
  email: string;
  status: 'pending_verification';
  /** Present only so the dev UI can surface it; see `verifyEmail`. */
  verificationToken?: string;
}

export const api = {
  me: () => request<MeResponse>('/me'),

  register: (input: {
    email: string;
    password: string;
    fullName: string;
    phone: string;
    acceptedTerms: boolean;
    acceptedPrivacy: boolean;
  }) =>
    request<RegisterResponse>('/auth/register', {
      method: 'POST',
      body: input,
    }),

  verifyEmail: (token: string) =>
    request<{ verified: true; alreadyVerified: boolean }>('/auth/verify-email', {
      method: 'POST',
      body: { token },
    }),

  login: (email: string, password: string) =>
    request<AuthResponse>('/auth/login', { method: 'POST', body: { email, password } }),

  listAjos: (status?: string) =>
    request<{ data: AjoSummary[]; page: { nextCursor: null; limit: number } }>(
      `/ajos${status ? `?status=${encodeURIComponent(status)}` : ''}`,
    ),

  getAjo: (id: string) => request<AjoDetail>(`/ajos/${id}`),

  createAjo: (input: {
    name: string;
    contributionKobo: number;
    currency: 'NGN';
    frequency: AjoFrequency;
    collectionDay: CollectionDay;
    durationRounds: number;
    maxMembers: number;
    startDate: string;
  }) => request<CreateAjoResult>('/ajos', { method: 'POST', body: input }),

  openEnrollment: (id: string) =>
    request<EnrollmentOpenResult>(`/ajos/${id}/activate`, {
      method: 'POST',
      body: { confirm: true },
    }),

  createInvite: (ajoId: string, contacts: { name?: string; email: string; phone?: string }[]) =>
    request<{ invitations: { id: string; email: string; status: string; token: string }[] }>(
      '/invitations',
      { method: 'POST', body: { ajoId, contacts } },
    ),

  listInvites: (ajoId: string) =>
    request<{ data: InvitationSummary[] }>(`/invitations?ajoId=${encodeURIComponent(ajoId)}`),

  previewInvite: (token: string) =>
    request<InvitationPreview>(`/invitations/${encodeURIComponent(token)}`),

  acceptInvite: (token: string) =>
    request<AcceptInvitationResult>('/invitations/accept', {
      method: 'POST',
      body: { token, accept: true, rulesAcknowledged: true },
    }),

  declineInvite: (token: string) =>
    request<{ declined: true }>(`/invitations/${encodeURIComponent(token)}/decline`, {
      method: 'POST',
    }),
};

/** Money in kobo → `₦1,000.00`, tabular, symbol attached (DESIGN §3). */
export function naira(kobo: number): string {
  const ngn = kobo / 100;
  const formatted = ngn.toLocaleString('en-NG', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `₦${formatted}`;
}

export function frequencyLabel(frequency: AjoFrequency | null): string {
  switch (frequency) {
    case 'WEEKLY':
      return 'Weekly';
    case 'BIWEEKLY':
      return 'Biweekly';
    case 'MONTHLY':
      return 'Monthly';
    default:
      return '—';
  }
}

export function dayLabel(day: CollectionDay | null): string {
  if (day === null) {
    return '—';
  }
  return day.charAt(0) + day.slice(1).toLowerCase();
}