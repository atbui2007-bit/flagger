import { supabase } from './supabase'

export const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export async function fetchJson<T>(path: string, init?: { method?: string; json?: unknown }): Promise<T> {
  // ngrok's free-tier domains serve an HTML interstitial to browser-looking
  // requests unless this header is present; irrelevant once on a real host.
  const headers: Record<string, string> = { 'ngrok-skip-browser-warning': 'true' }
  if (init?.json !== undefined) headers['Content-Type'] = 'application/json'
  if (supabase) {
    const { data } = await supabase.auth.getSession()
    const token = data.session?.access_token
    if (token) headers.Authorization = `Bearer ${token}`
  }
  const response = await fetch(`${API_BASE}${path}`, {
    method: init?.method ?? 'GET',
    headers,
    body: init?.json !== undefined ? JSON.stringify(init.json) : undefined,
  })
  if (response.status === 401 && supabase) {
    // Expired/invalid session: signing out flips the auth gate back to Login.
    void supabase.auth.signOut()
    throw new Error('Session expired')
  }
  if (!response.ok) throw new Error(`Request failed: ${response.status}`)
  return response.json() as Promise<T>
}

export function relativeDate(value?: string | null) {
  if (!value) return 'Not recorded'
  const seconds = Math.abs(Date.now() - new Date(value).getTime()) / 1000
  const future = new Date(value).getTime() > Date.now()
  const units: Array<[Intl.RelativeTimeFormatUnit, number]> = [['year',31536000],['month',2592000],['day',86400],['hour',3600],['minute',60]]
  const [unit, size] = units.find(([, divisor]) => seconds >= divisor) ?? ['minute', 60]
  return new Intl.RelativeTimeFormat('en', { numeric: 'auto' }).format(Math.max(1, Math.round(seconds / size)) * (future ? 1 : -1), unit)
}
