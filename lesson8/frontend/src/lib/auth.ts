'use client';
import { useEffect, useState } from 'react';

export interface AuthUser {
  id: string;
  email: string;
  role: 'candidate' | 'employer' | 'admin';
  displayName: string | null;
}

interface StoredSession {
  user: AuthUser;
  accessToken: string;
  refreshToken: string;
}

const KEY = 'w3c.session';

export function readSession(): StoredSession | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as StoredSession) : null;
  } catch {
    return null;
  }
}

export function writeSession(s: StoredSession) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(KEY, JSON.stringify(s));
  window.dispatchEvent(new Event('w3c-session-changed'));
}

export function clearSession() {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(KEY);
  window.dispatchEvent(new Event('w3c-session-changed'));
}

export function useSession(): { user: AuthUser | null; loading: boolean } {
  const [session, setSession] = useState<StoredSession | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    setSession(readSession());
    setLoading(false);
    const sync = () => setSession(readSession());
    window.addEventListener('w3c-session-changed', sync);
    window.addEventListener('storage', sync);
    return () => {
      window.removeEventListener('w3c-session-changed', sync);
      window.removeEventListener('storage', sync);
    };
  }, []);
  return { user: session?.user ?? null, loading };
}

export function getAccessToken(): string | null {
  return readSession()?.accessToken ?? null;
}
