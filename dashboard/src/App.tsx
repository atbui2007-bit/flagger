import { useEffect, useState } from 'react'
import ActivityFeed, { initialFilters, type Filters } from './components/ActivityFeed'
import Repositories from './components/Repositories'
import PullRequestDetail from './components/PullRequestDetail'
import Connect from './components/Connect'
import Settings from './components/Settings'
import Login from './components/Login'

type Route = { name: 'activity' | 'agents' | 'repositories' | 'settings' | 'connect' | 'login' } | { name: 'pr'; owner: string; repository: string; number: string }
function parseRoute(): Route {
  const path = location.hash.replace(/^#\/?/, '').replace(/\/$/, '')
  const pr = path.match(/^repos\/([^/]+)\/([^/]+)\/pr\/(\d+)$/)
  if (pr) return { name: 'pr', owner: decodeURIComponent(pr[1]), repository: decodeURIComponent(pr[2]), number: pr[3] }
  if (['activity', 'agents', 'repositories', 'settings', 'connect', 'login'].includes(path)) return { name: path as Exclude<Route, { name: 'pr' }>['name'] }
  return { name: 'activity' }
}
function navigate(path = '/') { location.hash = path === '/' ? '#/' : `#/${path.replace(/^\//, '')}` }

function getInitialTheme(): 'light' | 'dark' {
  const stored = localStorage.getItem('theme')
  if (stored === 'light' || stored === 'dark') return stored
  return 'dark' // dark-first: light is the explicit fallback, not the OS default
}

export default function App() {
  const [route, setRoute] = useState<Route>(parseRoute)
  const [filters, setFilters] = useState<Filters>(initialFilters)
  const [theme, setTheme] = useState<'light' | 'dark'>(getInitialTheme)
  useEffect(() => { document.documentElement.setAttribute('data-theme', theme); localStorage.setItem('theme', theme) }, [theme])
  useEffect(() => { const update = () => setRoute(parseRoute()); addEventListener('hashchange', update); return () => removeEventListener('hashchange', update) }, [])
  useEffect(() => { const label = route.name === 'pr' ? `Pull request #${route.number}` : route.name[0].toUpperCase() + route.name.slice(1); document.title = `${label} — Flagger` }, [route])
  const updateSearch = (value: string) => { setFilters((current) => ({ ...current, search: value })); if (route.name !== 'activity') navigate('/') }
  const viewRepository = (repository: string) => { setFilters((current) => ({ ...current, repository })); navigate('/') }
  if (route.name === 'login') return <Login onContinue={() => navigate('/')} />
  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="#/" aria-label="Flagger activity">Flagger</a>
      <label className="global-search"><span aria-hidden="true">⌕</span><input type="search" value={filters.search} onChange={(event) => updateSearch(event.target.value)} placeholder="Search activity" aria-label="Search activity" /></label>
      <nav aria-label="Primary navigation">
        {([['activity','Activity'],['repositories','Repositories'],['agents','Agents'],['settings','Settings']] as const).map(([name, label]) => <a key={name} className={route.name === name ? 'active' : ''} href={`#/${name}`}>{label}</a>)}
      </nav>
      <button type="button" className="icon-button theme-toggle" onClick={() => setTheme((current) => current === 'dark' ? 'light' : 'dark')} aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}>{theme === 'dark' ? '☀' : '☾'}</button>
    </aside>
    <div className="content">
      {(route.name === 'activity' || route.name === 'agents') && <ActivityFeed view={route.name} filters={filters} setFilters={setFilters} onNavigateActivity={() => navigate('/')} />}
      {route.name === 'repositories' && <Repositories onView={viewRepository} />}
      {route.name === 'settings' && <Settings />}{route.name === 'connect' && <Connect />}
      {route.name === 'pr' && <PullRequestDetail owner={route.owner} name={route.repository} number={route.number} />}
    </div>
  </div>
}
