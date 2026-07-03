import { useDeferredValue, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

interface Commit {
  id: string
  sha: string
  short_sha: string
  message: string
  url: string
  branch: string
  author_login: string
  agent_type: string
  attribution_confidence: string
  attribution_source: string
  risk_level: string | null
  risk_no_review: boolean
  risk_ci_unclean: boolean
  risk_sensitive_path: boolean
  risk_large_unreviewed: boolean
  risk_direct_to_main: boolean
  additions: number
  deletions: number
  full_name: string
  pushed_at: string
  git_ai_model?: string | null
}

interface ActivityResponse {
  data: Commit[]
  next_cursor: string | null
  has_more: boolean
}

interface SummaryResponse {
  total_commits: number
  ai_authored_commits: number
  ai_share_percent: number
  repositories: number
  review_needed: number
}

interface FacetsResponse {
  repositories: string[]
  contributors: string[]
  agents: string[]
}

type Filters = {
  repository: string
  contributor: string
  agent: string
  risk: string
  confidence: string
  search: string
}

const API_BASE = 'http://localhost:8000'
const initialFilters: Filters = {
  repository: '',
  contributor: '',
  agent: '',
  risk: '',
  confidence: '',
  search: '',
}

function queryString(filters: Filters, cursor?: string | null, includeLimit = true) {
  const params = new URLSearchParams()
  if (includeLimit) params.set('limit', '20')
  Object.entries(filters).forEach(([key, value]) => value && params.set(key, value))
  if (cursor) params.set('cursor', cursor)
  return params.toString()
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`)
  if (!response.ok) throw new Error(`Request failed: ${response.status}`)
  return response.json() as Promise<T>
}

function confidenceLabel(value: string) {
  const normalized = value.toLowerCase()
  if (normalized === 'high' || Number(value) >= 80) return 'High'
  if (normalized === 'medium' || Number(value) >= 50) return 'Medium'
  return 'Low'
}

function reviewState(commit: Commit) {
  if (commit.risk_no_review) return 'Needs review'
  if (commit.risk_level === 'low') return 'Approved'
  return 'Reviewed'
}

function dateGroup(value: string) {
  const date = new Date(value)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)
  if (date.toDateString() === today.toDateString()) return 'Today'
  if (date.toDateString() === yesterday.toDateString()) return 'Yesterday'
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric' }).format(date)
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('en', { hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}

function ActivitySkeleton() {
  return (
    <div className="ledger-skeleton" aria-label="Loading activity">
      {Array.from({ length: 8 }, (_, index) => <span key={index} />)}
    </div>
  )
}

function EvidenceInspector({ commit, onClose }: { commit: Commit; onClose: () => void }) {
  const signals = [
    [commit.risk_no_review, 'No review recorded'],
    [commit.risk_ci_unclean, 'CI is not clean'],
    [commit.risk_sensitive_path, 'Touches a sensitive path'],
    [commit.risk_large_unreviewed, 'Large unreviewed change'],
    [commit.risk_direct_to_main, 'Pushed directly to the default branch'],
  ].filter(([active]) => active)

  return (
    <aside className="evidence" aria-label="Commit evidence">
      <header className="evidence-header">
        <h2>Evidence</h2>
        <button className="icon-button" onClick={onClose} aria-label="Close evidence inspector">×</button>
      </header>
      <section className="evidence-section evidence-summary">
        <dl>
          <div><dt>Commit</dt><dd className="mono">{commit.sha}</dd></div>
          <div><dt>Repository / branch</dt><dd>{commit.full_name} / <span className="mono">{commit.branch}</span></dd></div>
          <div><dt>Author / agent</dt><dd>{commit.author_login} / {commit.agent_type}</dd></div>
          <div><dt>Attribution confidence</dt><dd>{confidenceLabel(commit.attribution_confidence)} · {commit.attribution_confidence}</dd></div>
        </dl>
      </section>
      <section className="evidence-section">
        <dl>
          <div><dt>Additions</dt><dd>+{commit.additions}</dd></div>
          <div><dt>Deletions</dt><dd>−{commit.deletions}</dd></div>
          <div><dt>Net lines</dt><dd>{commit.additions - commit.deletions >= 0 ? '+' : ''}{commit.additions - commit.deletions}</dd></div>
          <div><dt>Agent model</dt><dd>{commit.git_ai_model || 'Not reported'}</dd></div>
        </dl>
      </section>
      <section className="evidence-section">
        <h3>Review signals</h3>
        {signals.length ? (
          <ul className="signal-list">
            {signals.map(([, label]) => <li key={String(label)}><span aria-hidden="true">◇</span>{label}</li>)}
          </ul>
        ) : <p className="quiet-copy">No review signals detected. This is not a guarantee of safety.</p>}
      </section>
      <section className="evidence-section">
        <h3>Checks &amp; reviews</h3>
        <dl>
          <div><dt>CI status</dt><dd>{commit.risk_ci_unclean ? 'Not clean' : 'No issue reported'}</dd></div>
          <div><dt>Code review</dt><dd>{commit.risk_no_review ? 'No review recorded' : 'Review recorded'}</dd></div>
          <div><dt>Assessment</dt><dd>Heuristic signal</dd></div>
        </dl>
      </section>
      <section className="evidence-section evidence-links">
        <h3>Links</h3>
        <a href={commit.url} target="_blank" rel="noreferrer">View commit <span aria-hidden="true">↗</span></a>
      </section>
    </aside>
  )
}

function ActivityFeed() {
  const [filters, setFilters] = useState(initialFilters)
  const [cursor, setCursor] = useState<string | null>(null)
  const [cursorHistory, setCursorHistory] = useState<Array<string | null>>([])
  const [selected, setSelected] = useState<Commit | null>(null)
  const [summaryExpanded, setSummaryExpanded] = useState(false)
  const deferredSearch = useDeferredValue(filters.search)
  const queryFilters = { ...filters, search: deferredSearch }

  const activity = useQuery<ActivityResponse>({
    queryKey: ['activity', queryFilters, cursor],
    queryFn: () => fetchJson(`/activity/recent?${queryString(queryFilters, cursor)}`),
  })
  const summary = useQuery<SummaryResponse>({
    queryKey: ['activity-summary', queryFilters],
    queryFn: () => fetchJson(`/activity/summary?${queryString(queryFilters, null, false)}`),
  })
  const facets = useQuery<FacetsResponse>({
    queryKey: ['activity-facets'],
    queryFn: () => fetchJson('/activity/facets'),
  })

  const groups = useMemo(() => {
    const result = new Map<string, Commit[]>()
    activity.data?.data.forEach((commit) => {
      const group = dateGroup(commit.pushed_at)
      result.set(group, [...(result.get(group) || []), commit])
    })
    return [...result.entries()]
  }, [activity.data])

  function updateFilter(key: keyof Filters, value: string) {
    setFilters((current) => ({ ...current, [key]: value }))
    setCursor(null)
    setCursorHistory([])
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Flagger activity">Flagger</a>
        <nav aria-label="Primary navigation">
          <a className="active" href="#activity">Activity</a>
          <a href="#repositories">Repositories</a>
          <a href="#agents">Agents</a>
          <a href="#settings">Settings</a>
        </nav>
        <label className="global-search"><span aria-hidden="true">⌕</span><input type="search" value={filters.search} onChange={(event) => updateFilter('search', event.target.value)} placeholder="Search commits, repositories, authors" aria-label="Search activity" /></label>
      </header>

      <section className="summary" aria-label="Activity summary">
        <div className="summary-primary">
          <div><strong>{summary.data ? `${summary.data.ai_share_percent}%` : '—'}</strong><span>AI-authored</span></div>
          <div><strong>{summary.data?.review_needed ?? '—'}</strong><span>Needs review</span></div>
          <div><strong>{summary.data?.total_commits ?? '—'}</strong><span>Commits</span></div>
        </div>
        {summaryExpanded && (
          <div className="summary-secondary">
            <span>{summary.data?.repositories ?? '—'} repositories</span>
            <span>{summary.data?.ai_authored_commits ?? '—'} agent commits</span>
          </div>
        )}
        <button className="summary-toggle" onClick={() => setSummaryExpanded((value) => !value)} aria-expanded={summaryExpanded}>
          {summaryExpanded ? 'Fewer details' : 'More details'} <span aria-hidden="true">⌄</span>
        </button>
      </section>

      <main className={`workspace${selected ? ' has-inspector' : ''}`} id="activity">
        <section className="activity-pane" aria-labelledby="activity-title">
          <div className="activity-heading">
            <div><h1 id="activity-title">Activity</h1><p>AI-authored changes across connected repositories</p></div>
            {selected && <span className="update-status" aria-live="polite">Updates paused while reviewing</span>}
          </div>

          <div className="filters" aria-label="Activity filters">
            <label><span className="sr-only">Repository</span><select value={filters.repository} onChange={(e) => updateFilter('repository', e.target.value)}><option value="">All repositories</option>{facets.data?.repositories.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
            <label><span className="sr-only">Contributor</span><select value={filters.contributor} onChange={(e) => updateFilter('contributor', e.target.value)}><option value="">All contributors</option>{facets.data?.contributors.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
            <label><span className="sr-only">Agent</span><select value={filters.agent} onChange={(e) => updateFilter('agent', e.target.value)}><option value="">All agents</option>{facets.data?.agents.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
            <label><span className="sr-only">Risk signal</span><select value={filters.risk} onChange={(e) => updateFilter('risk', e.target.value)}><option value="">Any risk signal</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></label>
            <label><span className="sr-only">Confidence</span><select value={filters.confidence} onChange={(e) => updateFilter('confidence', e.target.value)}><option value="">Any confidence</option><option value="high">High confidence</option><option value="medium">Medium confidence</option><option value="low">Low confidence</option></select></label>
          </div>

          <div className="ledger" role="table" aria-label="Commit activity">
            <div className="ledger-head" role="row">
              <span role="columnheader">Time</span><span role="columnheader">Change</span><span role="columnheader">Repository / branch</span><span role="columnheader">Author / agent</span><span role="columnheader">Confidence</span><span role="columnheader">Changes</span><span role="columnheader">State</span>
            </div>
            {activity.isPending && <ActivitySkeleton />}
            {activity.isError && <div className="state-message"><strong>Activity could not be loaded.</strong><span>Check that the API is running, then try again.</span><button onClick={() => activity.refetch()}>Retry</button></div>}
            {!activity.isPending && !activity.isError && groups.length === 0 && <div className="state-message"><strong>No activity matches these filters.</strong><span>Clear a filter to broaden the ledger.</span><button onClick={() => setFilters(initialFilters)}>Clear filters</button></div>}
            {groups.map(([group, commits]) => (
              <section className="ledger-group" key={group} aria-label={group}>
                <h2>{group}</h2>
                {commits.map((commit) => {
                  const state = reviewState(commit)
                  const confidence = confidenceLabel(commit.attribution_confidence)
                  return (
                    <div className={`ledger-row${selected?.id === commit.id ? ' selected' : ''}`} role="row" tabIndex={0} key={commit.id} onClick={() => setSelected(commit)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); setSelected(commit) } }} aria-label={`Inspect ${commit.message}`}>
                      <span className="row-time" role="cell">{formatTime(commit.pushed_at)}</span>
                      <span className="row-change" role="cell"><strong>{commit.message}</strong><code>{commit.short_sha}</code></span>
                      <span className="row-repo" role="cell"><strong>{commit.full_name}</strong><small>{commit.branch}</small></span>
                      <span className="row-author" role="cell"><strong>{commit.author_login}</strong><small>{commit.agent_type}</small></span>
                      <span className={`confidence confidence-${confidence.toLowerCase()}`} role="cell"><i aria-hidden="true" /><span>{confidence}</span><small>{commit.attribution_confidence}</small></span>
                      <span className="row-diff mono" role="cell">+{commit.additions} −{commit.deletions}</span>
                      <span className={`review-state state-${state.toLowerCase().replace(' ', '-')}`} role="cell"><i aria-hidden="true" />{state}</span>
                    </div>
                  )
                })}
              </section>
            ))}
          </div>
          {(activity.data?.has_more || cursorHistory.length > 0) && <footer className="pagination"><span>Showing {activity.data?.data.length ?? 0} changes</span><div>{cursorHistory.length > 0 && <button className="secondary-button" onClick={() => { const previous = cursorHistory[cursorHistory.length - 1] ?? null; setCursor(previous); setCursorHistory((history) => history.slice(0, -1)) }}>Previous</button>}{activity.data?.has_more && <button onClick={() => { setCursorHistory((history) => [...history, cursor]); setCursor(activity.data?.next_cursor || null) }}>Next page</button>}</div></footer>}
        </section>
        {selected && <EvidenceInspector commit={selected} onClose={() => setSelected(null)} />}
      </main>
    </div>
  )
}

export default ActivityFeed
