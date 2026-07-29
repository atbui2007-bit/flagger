import { useEffect, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import ActivityFeed, { initialFilters, type Filters } from './components/ActivityFeed'
import Repositories from './components/Repositories'
import PullRequestDetail from './components/PullRequestDetail'
import Connect from './components/Connect'
import Onboarding from './components/Onboarding'
import Settings from './components/Settings'
import Login from './components/Login'
import { useSession, getPendingInstallation, clearPendingInstallation, getProviderToken } from './lib/auth'
import { fetchJson } from './lib/api'

interface Installation {
  github_installation_id: number
}

type Route = { name: 'activity' | 'agents' | 'repositories' | 'settings' | 'connect' | 'login' | 'onboarding' } | { name: 'pr'; owner: string; repository: string; number: string }
function parseRoute(): Route {
  const path = location.hash.replace(/^#\/?/, '').replace(/\/$/, '')
  const pr = path.match(/^repos\/([^/]+)\/([^/]+)\/pr\/(\d+)$/)
  if (pr) return { name: 'pr', owner: decodeURIComponent(pr[1]), repository: decodeURIComponent(pr[2]), number: pr[3] }
  if (['activity', 'agents', 'repositories', 'settings', 'connect', 'login', 'onboarding'].includes(path)) return { name: path as Exclude<Route, { name: 'pr' }>['name'] }
  return { name: 'activity' }
}
function navigate(path = '/') { location.hash = path === '/' ? '#/' : `#/${path.replace(/^\//, '')}` }

function Splash() {
  return <main className="login-page" aria-label="Loading Flagger"><div className="login-panel">
    <a className="login-brand" href="#/">Flagger</a>
    <p className="login-lede">Preparing your ledger.</p>
    <div className="ledger-skeleton" aria-label="Loading"><span /><span /></div>
  </div></main>
}

function getInitialTheme(): 'light' | 'dark' {
  const stored = localStorage.getItem('theme')
  if (stored === 'light' || stored === 'dark') return stored
  return 'dark' // dark-first: light is the explicit fallback, not the OS default
}

export default function App() {
  const auth = useSession()
  const queryClient = useQueryClient()
  const [route, setRoute] = useState<Route>(parseRoute)
  const [filters, setFilters] = useState<Filters>(initialFilters)
  const [theme, setTheme] = useState<'light' | 'dark'>(getInitialTheme)
  const userId = auth.status === 'signed-in' ? auth.session.user.id : null
  const [syncedUser, setSyncedUser] = useState<string | null>(null)
  const syncing = useRef<string | null>(null)
  const syncSettled = Boolean(userId) && syncedUser === userId
  const installations = useQuery<{ data: Installation[] }>({
    queryKey: ['installations'],
    queryFn: () => fetchJson('/installations'),
    enabled: auth.status === 'signed-in' && syncSettled,
  })
  const connected = (installations.data?.data.length ?? 0) > 0

  useEffect(() => { document.documentElement.setAttribute('data-theme', theme); localStorage.setItem('theme', theme) }, [theme])
  useEffect(() => { const update = () => setRoute(parseRoute()); addEventListener('hashchange', update); return () => removeEventListener('hashchange', update) }, [])
  useEffect(() => { const label = route.name === 'pr' ? `Pull request #${route.number}` : route.name[0].toUpperCase() + route.name.slice(1); document.title = `${label} — Flagger` }, [route])
  useEffect(() => {
    if (auth.status !== 'signed-out') return
    queryClient.clear()
    setSyncedUser(null)
    syncing.current = null
  }, [auth.status, queryClient])
  useEffect(() => {
    // A GitHub App install redirect stashed a pending installation id; route it
    // to Onboarding, which performs the claim. While signed-out the id just waits
    // in sessionStorage for the login gate to clear.
    if (!getPendingInstallation()) return
    if (auth.status === 'signed-in') navigate('/onboarding')
    // Claim is unavailable without auth, so Onboarding has nothing to do -- and it
    // renders full-bleed with a sign-out button that no-ops when supabase is null.
    // Send local-dev straight to Connect, which lives inside the navigable shell.
    if (auth.status === 'disabled') { clearPendingInstallation(); navigate('/connect') }
  }, [auth.status])
  useEffect(() => {
    if (!userId || syncedUser === userId || syncing.current === userId) return
    const providerToken = getProviderToken()
    if (!providerToken) {
      setSyncedUser(userId)
      return
    }
    syncing.current = userId
    const settle = () => { syncing.current = null; setSyncedUser(userId) }
    // ponytail: the onboarding gate waits on this, so a hung request would strand the
    // user on the splash. 8s cap, then route on whatever /installations already knows.
    const timer = setTimeout(settle, 8000)
    void fetchJson('/installations/sync-access', {
      method: 'POST',
      json: { provider_token: providerToken },
    }).then(() => {
      void queryClient.invalidateQueries({ queryKey: ['installations'] })
      void queryClient.invalidateQueries({ queryKey: ['activity'] })
      void queryClient.invalidateQueries({ queryKey: ['activity-summary'] })
      void queryClient.invalidateQueries({ queryKey: ['activity-facets'] })
      void queryClient.invalidateQueries({ queryKey: ['agent-breakdown'] })
      void queryClient.invalidateQueries({ queryKey: ['repository-summary'] })
      void queryClient.invalidateQueries({ queryKey: ['repos'] })
    }).catch(() => {}).finally(() => {
      clearTimeout(timer)
      settle()
    })
    return () => clearTimeout(timer)
  }, [queryClient, syncedUser, userId])
  useEffect(() => {
    if (auth.status !== 'signed-in' || !syncSettled || installations.isError || !installations.data) return
    if (!connected && route.name !== 'onboarding' && route.name !== 'settings') navigate('/onboarding')
    if (connected && route.name === 'onboarding' && !getPendingInstallation()) navigate('/')
  }, [auth.status, connected, installations.data, installations.isError, route.name, syncSettled])

  const updateSearch = (value: string) => { setFilters((current) => ({ ...current, search: value })); if (route.name !== 'activity') navigate('/') }
  const viewRepository = (repository: string) => { setFilters((current) => ({ ...current, repository })); navigate('/') }
  const routeKey = route.name === 'pr' ? `${route.name}-${route.number}` : route.name
  if (auth.status === 'loading') return <div className="route-view" key="loading"><Splash /></div>
  if (auth.status === 'signed-out') return <div className="route-view" key="login"><Login onContinue={() => navigate('/')} /></div>
  if (route.name === 'login') return <div className="route-view" key={routeKey}><Login onContinue={() => navigate('/')} /></div>
  if (auth.status === 'signed-in' && !installations.data && !installations.isError) return <div className="route-view" key="loading"><Splash /></div>
  if (route.name === 'onboarding') return <div className="route-view" key={routeKey}><Onboarding /></div>
  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="#/" aria-label="Flagger activity"><span className="brand-mark" aria-hidden="true"><i className="brand-dot brand-dot-blue" /><i className="brand-dot brand-dot-violet" /><i className="brand-dot brand-dot-cyan" /></span><span>Flagger</span></a>
      <label className="global-search"><span aria-hidden="true">⌕</span><input type="search" value={filters.search} onChange={(event) => updateSearch(event.target.value)} placeholder="Search activity" aria-label="Search activity" /></label>
      <nav aria-label="Primary navigation">
        {([['activity','Activity'],['repositories','Repositories'],['agents','Agents'],['settings','Settings']] as const).map(([name, label]) => <a key={name} className={route.name === name ? 'active' : ''} href={`#/${name}`}>{label}</a>)}
      </nav>
      <button type="button" className="icon-button theme-toggle" onClick={() => setTheme((current) => current === 'dark' ? 'light' : 'dark')} aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}>{theme === 'dark' ? '☀' : '☾'}</button>
    </aside>
    <div className="content">
      <div className="route-view" key={routeKey}>
      {(route.name === 'activity' || route.name === 'agents') && <ActivityFeed view={route.name} filters={filters} setFilters={setFilters} onNavigateActivity={() => navigate('/')} />}
      {route.name === 'repositories' && <Repositories onView={viewRepository} />}
      {route.name === 'settings' && <Settings />}{route.name === 'connect' && <Connect />}
      {route.name === 'pr' && <PullRequestDetail owner={route.owner} name={route.repository} number={route.number} />}
      </div>
    </div>
  </div>
}
