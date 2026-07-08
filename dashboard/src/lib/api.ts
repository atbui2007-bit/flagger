export const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`)
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
