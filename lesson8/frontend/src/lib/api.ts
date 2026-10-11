export interface JobSummary {
  id: string;
  slug: string;
  title: string;
  location: string | null;
  isRemote: boolean;
  salaryMin: number | null;
  salaryMax: number | null;
  salaryCurrency: string;
  postedAt: string;
  applyUrl: string | null;
  applyType: 'external' | 'internal';
  company: { id: string; slug: string; name: string; logoUrl: string | null } | null;
  tags: Array<{ slug: string; name: string; category: string }>;
}

export interface JobDetail extends JobSummary {
  description: string;
  seniority: string | null;
  employmentType: string | null;
  viewsCount: number;
  expiresAt: string;
}

export interface Pagination { page: number; limit: number; total: number; totalPages: number; }
export interface Paginated<T> { data: T[]; meta: { pagination: Pagination } }

export interface TagDto { id: string; slug: string; name: string; category: string; count?: number; }
export interface CompanySummary {
  id: string; slug: string; name: string; logoUrl: string | null;
  description: string | null; hqCity: string | null; hqCountry: string | null;
  sizeBucket: string | null; openRolesCount: number;
  fundingTotalUsd: number | null;
}
export interface CompanyDetail extends CompanySummary {
  website: string | null;
  twitter: string | null; discord: string | null; linkedin: string | null; github: string | null;
  foundedYear: number | null;
  jobs: JobSummary[];
}

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:4000/v1';

async function get<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json', ...(init?.headers as any ?? {}) };
  if (typeof window !== 'undefined') {
    try {
      const raw = window.localStorage.getItem('w3c.session');
      if (raw) {
        const sess = JSON.parse(raw);
        if (sess?.accessToken) headers.Authorization = `Bearer ${sess.accessToken}`;
      }
    } catch { /* ignore */ }
  }
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers,
    next: { revalidate: 30 },
  });
  if (!res.ok) {
    let detail = '';
    try { detail = JSON.stringify(await res.json()); } catch { /* ignore */ }
    throw new Error(`API ${res.status} ${path} ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  jobs: {
    list: (params: { page?: number; limit?: number; tag?: string; remote?: boolean; q?: string; company?: string; sort?: 'recent' | 'salary' } = {}) => {
      const search = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== '') search.set(k, String(v)); });
      const qs = search.toString();
      return get<Paginated<JobSummary>>(`/jobs${qs ? '?' + qs : ''}`);
    },
    bySlug: (slug: string) => get<JobDetail>(`/jobs/${slug}`),
  },
  companies: {
    list: (params: { page?: number; limit?: number; q?: string } = {}) => {
      const search = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== '') search.set(k, String(v)); });
      const qs = search.toString();
      return get<Paginated<CompanySummary>>(`/companies${qs ? '?' + qs : ''}`);
    },
    bySlug: (slug: string) => get<CompanyDetail>(`/companies/${slug}`),
  },
  tags: {
    popular: (limit = 60) => get<TagDto[]>(`/tags?popular=true&limit=${limit}`),
  },
};

export async function subscribe(payload: { email: string; firstName?: string; lastName?: string; source?: string }) {
  const res = await fetch(`${BASE}/subscribe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`subscribe failed: ${res.status}`);
  return res.json();
}

export async function authLogin(payload: { email: string; password: string }) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: { message: 'Login failed' } }));
    throw new Error(err.error?.message ?? 'Login failed');
  }
  return res.json();
}

export async function authRegister(payload: { email: string; password: string; role: 'candidate' | 'employer'; displayName?: string; companyName?: string }) {
  const res = await fetch(`${BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: { message: 'Register failed' } }));
    throw new Error(err.error?.message ?? 'Register failed');
  }
  return res.json();
}

export interface ArticleDto {
  id: string;
  slug: string;
  title: string;
  category: string;
  author: string;
  excerpt: string;
  contentMd: string;
  coverGradient: string | null;
  readMinutes: number | null;
  isFree: boolean;
  externalUrl: string | null;
  publishedAt: string;
}

export interface SalarySnapshot {
  overall: { job_count: number; avg_min: number; avg_max: number; min_min: number; max_max: number } | null;
  byRole: Array<{ slug: string; name: string; job_count: number; avg_min: number; avg_max: number; min_min: number; max_max: number }>;
  bySeniority: Array<{ seniority: string; job_count: number; avg_min: number; avg_max: number }>;
  byRemote: Array<{ kind: 'remote' | 'onsite'; job_count: number; avg_min: number; avg_max: number }>;
  updatedAt: string;
}

export const articlesApi = {
  list: (params: { category?: string; limit?: number } = {}) => {
    const usp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined) usp.set(k, String(v)); });
    return get<Paginated<ArticleDto>>(`/articles${usp.toString() ? '?' + usp.toString() : ''}`);
  },
  bySlug: (slug: string) => get<ArticleDto>(`/articles/${slug}`),
};

export const salariesApi = {
  snapshot: () => get<SalarySnapshot>('/salaries'),
};

export interface CreateJobInput {
  title: string;
  description: string;
  location?: string;
  isRemote: boolean;
  seniority?: 'intern' | 'junior' | 'mid' | 'senior' | 'lead' | 'exec';
  employmentType?: 'full_time' | 'part_time' | 'contract' | 'internship';
  salaryMin?: number;
  salaryMax?: number;
  applyType: 'external' | 'internal';
  applyUrl?: string;
  applicationEmail?: string;
  tags: string[];
}

export async function createJob(input: CreateJobInput) {
  const raw = typeof window !== 'undefined' ? window.localStorage.getItem('w3c.session') : null;
  const token = raw ? JSON.parse(raw)?.accessToken : null;
  const res = await fetch(`${BASE}/jobs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: { message: 'Create failed' } }));
    throw new Error(err.error?.message ?? 'Create failed');
  }
  return res.json();
}

export async function getMe() {
  const raw = typeof window !== 'undefined' ? window.localStorage.getItem('w3c.session') : null;
  const token = raw ? JSON.parse(raw)?.accessToken : null;
  if (!token) throw new Error('Not signed in');
  const res = await fetch(`${BASE}/users/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Not signed in');
  return res.json();
}
