import { useDeferredValue, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchJson } from '../lib/api'

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

interface AgentSummary {
  agent_type: string
  commits: number
  repositories: number
  contributors: number
  review_needed: number
  certain_attribution: number
  additions: number
  deletions: number
  last_active: string
  sources: string[]
}

interface AgentsResponse { data: AgentSummary[] }

export type Filters = {
  repository: string
  contributor: string
  agent: string
  risk: string
  confidence: string
  search: string
}

export const initialFilters: Filters = {
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

function confidenceLabel(value: string) {
  const normalized = value.toLowerCase()
  if (normalized === 'certain' || normalized === 'high' || Number(value) >= 80) return 'High'
  if (normalized === 'likely' || normalized === 'medium' || Number(value) >= 50) return 'Medium'
  return 'Low'
}

function formatAgentName(value: string) {
  if (value.toLowerCase() === 'human') return 'Human-authored'
  if (value.toLowerCase() === 'unknown') return 'Unknown agent'
  return value
}

function AgentBreakdown({ onInspect }: { onInspect: (agent: string) => void }) {
  const agents = useQuery<AgentsResponse>({
    queryKey: ['agent-breakdown'],
    queryFn: () => fetchJson('/activity/agents'),
  })
  const total = agents.data?.data.reduce((sum, agent) => sum + agent.commits, 0) ?? 0

  return (
    <main className="agents-workspace" id="agents">
      <div className="agents-heading">
        <div><h1>Agents</h1><p>Attribution, review coverage, and repository reach by authoring agent</p></div>
        <span>{agents.data?.data.length ?? '—'} identities observed</span>
      </div>
      <div className="agents-ledger" role="table" aria-label="Agent activity breakdown">
        <div className="agents-head" role="row">
          <span role="columnheader">Agent</span><span role="columnheader">Commits</span><span role="columnheader">Share</span><span role="columnheader">Coverage</span><span role="columnheader">Attribution</span><span role="columnheader">Review state</span><span role="columnheader">Last active</span>
        </div>
        {agents.isPending && <ActivitySkeleton />}
        {agents.isError && <div className="state-message"><strong>Agent activity could not be loaded.</strong><span>Check that the API is running, then try again.</span><button onClick={() => agents.refetch()}>Retry</button></div>}
        {agents.data?.data.map((agent) => {
          const share = total ? Math.round((agent.commits / total) * 100) : 0
          const certain = agent.commits ? Math.round((agent.certain_attribution / agent.commits) * 100) : 0
          return (
            <button className="agent-row" role="row" key={agent.agent_type} onClick={() => onInspect(agent.agent_type)} aria-label={`View ${agent.agent_type} activity`}>
              <span className="agent-identity" role="cell"><i aria-hidden="true">{formatAgentName(agent.agent_type).slice(0, 1).toUpperCase()}</i><span><strong>{formatAgentName(agent.agent_type)}</strong><small>{agent.sources.join(' · ').replace(/_/g, ' ')}</small></span></span>
              <strong className="agent-count mono" role="cell">{agent.commits}</strong>
              <span className="agent-share" role="cell"><span><i style={{ width: `${share}%` }} /></span><small>{share}%</small></span>
              <span className="agent-detail" role="cell"><strong>{agent.repositories} repos</strong><small>{agent.contributors} contributors</small></span>
              <span className="agent-detail" role="cell"><strong>{certain}% certain</strong><small>{agent.commits - agent.certain_attribution} suspected</small></span>
              <span className={`review-state ${agent.review_needed ? 'state-needs-review' : 'state-approved'}`} role="cell"><i aria-hidden="true" />{agent.review_needed ? `${agent.review_needed} need review` : 'Reviewed'}</span>
              <span className="agent-last-active" role="cell">{dateGroup(agent.last_active)}<small>+{agent.additions} −{agent.deletions}</small></span>
            </button>
          )
        })}
      </div>
      <p className="agents-note">Attribution labels report the evidence available to Flagger. “Certain” indicates direct provenance such as git-ai notes; suspected matches remain explicitly separate.</p>
    </main>
  )
}

function reviewState(commit: Commit) {
  const hasHardRisk = commit.risk_ci_unclean || commit.risk_sensitive_path || commit.risk_large_unreviewed || commit.risk_direct_to_main
  if (commit.risk_level === 'low' && !commit.risk_no_review && !hasHardRisk) return 'Approved'
  if (commit.risk_no_review) return 'Pending review'
  if (hasHardRisk) return 'Flagged'
  return 'Review needed'
}

function reviewStateClass(commit: Commit) {
  const state = reviewState(commit)
  if (state === 'Approved') return 'state-approved'
  if (state === 'Pending review') return 'state-pending'
  if (state === 'Flagged') return 'state-flagged'
  return 'state-review'
}

function buildReasonChips(commit: Commit) {
  const reasons = []
  if (commit.risk_large_unreviewed || commit.additions + commit.deletions > 300) reasons.push('Large diff')
  if (commit.risk_no_review) reasons.push('No review')
  if (commit.risk_ci_unclean) reasons.push('CI not clean')
  if (commit.risk_sensitive_path) reasons.push('Sensitive file')
  if (commit.risk_direct_to_main) reasons.push('Direct to main')
  return reasons
}

function reviewPriority(commit: Commit) {
  let score = 0
  if (commit.risk_direct_to_main) score += 500
  if (commit.risk_sensitive_path) score += 420
  if (commit.risk_ci_unclean) score += 360
  if (commit.risk_large_unreviewed) score += 320
  if (commit.risk_no_review) score += 240
  switch (commit.risk_level?.toLowerCase()) {
    case 'high': score += 180; break
    case 'medium': score += 120; break
    case 'low': score += 60; break
    default: score += 20; break
  }
  const confidence = Number(commit.attribution_confidence)
  score += Number.isFinite(confidence) ? Math.min(Math.max(confidence, 0), 100) : 0
  return score
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

function ActivityFeed({ view, filters, setFilters, onNavigateActivity }: {
  view: 'activity' | 'agents'
  filters: Filters
  setFilters: React.Dispatch<React.SetStateAction<Filters>>
  onNavigateActivity: () => void
}) {
  const [cursor, setCursor] = useState<string | null>(null)
  const [cursorHistory, setCursorHistory] = useState<Array<string | null>>([])
  const [selected, setSelected] = useState<Commit | null>(null)
  const [summaryExpanded, setSummaryExpanded] = useState(false)
  const [insightOpen, setInsightOpen] = useState(false)
  const [sortMode, setSortMode] = useState<'priority' | 'recent'>('priority')
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
    const commits = [...(activity.data?.data ?? [])]
    if (sortMode === 'priority') {
      commits.sort((a, b) => {
        const priority = reviewPriority(b) - reviewPriority(a)
        if (priority !== 0) return priority
        return new Date(b.pushed_at).getTime() - new Date(a.pushed_at).getTime()
      })
    } else {
      commits.sort((a, b) => new Date(b.pushed_at).getTime() - new Date(a.pushed_at).getTime())
    }

    const result = new Map<string, Commit[]>()
    commits.forEach((commit) => {
      const group = dateGroup(commit.pushed_at)
      result.set(group, [...(result.get(group) || []), commit])
    })
    return [...result.entries()]
  }, [activity.data, sortMode])

  function updateFilter(key: keyof Filters, value: string) {
    setFilters((current) => ({ ...current, [key]: value }))
    setCursor(null)
    setCursorHistory([])
  }

  function inspectAgent(agent: string) {
    updateFilter('agent', agent)
    onNavigateActivity()
  }

  const summaryAiShare = summary.isPending ? null : summary.data?.ai_share_percent ?? 0
  const summaryReviewNeeded = summary.isPending ? null : summary.data?.review_needed ?? 0
  const summaryTotalCommits = summary.isPending ? null : summary.data?.total_commits ?? 0
  const summaryRepositories = summary.isPending ? null : summary.data?.repositories ?? 0
  const summaryAgentCommits = summary.isPending ? null : summary.data?.ai_authored_commits ?? 0
  const activityErrorMessage = activity.error instanceof Error ? activity.error.message : 'Unknown error'

  return (
    <>
      {view === 'activity' && <section className="summary" aria-label="Activity summary">
        <button type="button" className={`summary-visual${insightOpen ? ' insight-open' : ''}`} onClick={() => setInsightOpen((value) => !value)} onMouseEnter={() => setInsightOpen(true)} onMouseLeave={() => setInsightOpen(false)} aria-expanded={insightOpen}>
          <div className="summary-chart" aria-hidden="true">
            {[44, 68, 56, 82, 64, 90].map((height, index) => (
              <span key={index} style={{ height: `${height}%`, animationDelay: `${index * 0.1}s` }} />
            ))}
          </div>
          <div className="summary-visual-copy">
            <strong>Velocity</strong>
            <span>{summary.isPending ? 'Measuring recent delivery patterns…' : 'Signals from review load, commit volume, and AI share'}</span>
          </div>
        </button>
        <div className="summary-primary">
          <button type="button" className="stat-chip" data-populated={!summary.isPending && summaryAiShare > 0} onClick={() => setSummaryExpanded(true)}>
            <span className="stat-chip-icon" aria-hidden="true">✦</span>
            <strong>{summary.isPending ? <span className="stat-value-skeleton" aria-hidden="true" /> : `${summaryAiShare}%`}</strong>
            <span>AI-authored</span>
          </button>
          <button type="button" className="stat-chip" data-populated={!summary.isPending && summaryReviewNeeded > 0} onClick={() => setSummaryExpanded(true)}>
            <span className="stat-chip-icon" aria-hidden="true">⚑</span>
            <strong>{summary.isPending ? <span className="stat-value-skeleton" aria-hidden="true" /> : summaryReviewNeeded}</strong>
            <span>Needs review</span>
          </button>
          <button type="button" className="stat-chip" data-populated={!summary.isPending && summaryTotalCommits > 0} onClick={() => setSummaryExpanded(true)}>
            <span className="stat-chip-icon" aria-hidden="true">⟲</span>
            <strong>{summary.isPending ? <span className="stat-value-skeleton" aria-hidden="true" /> : summaryTotalCommits}</strong>
            <span>Commits</span>
          </button>
        </div>
        {summaryExpanded && (
          <div className="summary-secondary">
            <span>{summaryRepositories} repositories</span>
            <span>{summaryAgentCommits} agent commits</span>
          </div>
        )}
        {insightOpen && (
          <div className="summary-insight" role="dialog" aria-label="Velocity explanation">
            <strong>What this gauges</strong>
            <p>Velocity is a lightweight signal derived from recent commit volume, review backlog, and how much of the work appears AI-authored. It is meant to highlight momentum and coordination pressure, not to declare success.</p>
            <small>Hover or click the panel to reopen this explanation whenever you need context.</small>
          </div>
        )}
        <button className="summary-toggle" onClick={() => setSummaryExpanded((value) => !value)} aria-expanded={summaryExpanded}>
          {summaryExpanded ? 'Fewer details' : 'More details'} <span aria-hidden="true">⌄</span>
        </button>
      </section>}

      {view === 'agents' ? <AgentBreakdown onInspect={inspectAgent} /> : <main className={`workspace${selected ? ' has-inspector' : ''}`} id="activity">
        <section className="activity-pane" aria-labelledby="activity-title">
          <div className="activity-heading">
            <div><h1 id="activity-title">Activity</h1><p>AI-authored changes across connected repositories</p></div>
            {selected && <span className="update-status" aria-live="polite">Updates paused while reviewing</span>}
          </div>

          <div className="filters" aria-label="Activity filters">
            <label className="filter-pill"><span className="sr-only">Repository</span><select value={filters.repository} onChange={(e) => updateFilter('repository', e.target.value)}><option value="">All repositories</option>{facets.data?.repositories.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
            <label className="filter-pill"><span className="sr-only">Contributor</span><select value={filters.contributor} onChange={(e) => updateFilter('contributor', e.target.value)}><option value="">All contributors</option>{facets.data?.contributors.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
            <label className="filter-pill"><span className="sr-only">Agent</span><select value={filters.agent} onChange={(e) => updateFilter('agent', e.target.value)}><option value="">All agents</option>{facets.data?.agents.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
            <label className="filter-pill"><span className="sr-only">Risk signal</span><select value={filters.risk} onChange={(e) => updateFilter('risk', e.target.value)}><option value="">Any risk signal</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></label>
            <label className="filter-pill"><span className="sr-only">Confidence</span><select value={filters.confidence} onChange={(e) => updateFilter('confidence', e.target.value)}><option value="">Any confidence</option><option value="high">High confidence</option><option value="medium">Medium confidence</option><option value="low">Low confidence</option></select></label>
          </div>

          <div className="filter-hint">
            <span>Review queue default: sorted by risk and confidence so the highest-priority items surface first.</span>
            <button type="button" className={`queue-button${sortMode === 'priority' ? ' active' : ''}`} onClick={() => setSortMode('priority')}>Review queue</button>
            <button type="button" className={`queue-button${sortMode === 'recent' ? ' active' : ''}`} onClick={() => setSortMode('recent')}>Latest first</button>
          </div>

          <div className="ledger" role="table" aria-label="Commit activity">
            <div className="ledger-head" role="row">
              <span role="columnheader">Time</span><span role="columnheader">Change</span><span role="columnheader">Repository / branch</span><span role="columnheader">Author / agent</span><span role="columnheader">Confidence</span><span role="columnheader">Changes</span><span role="columnheader">State</span>
            </div>
            {activity.isPending && (
              <div className="state-card state-card-loading">
                <div className="state-card-icon" aria-hidden="true">◌</div>
                <div className="state-card-copy">
                  <strong>Loading activity…</strong>
                  <span>Fetching the latest review signals and commit history.</span>
                </div>
              </div>
            )}
            {activity.isPending && <ActivitySkeleton />}
            {activity.isError && (
              <div className="state-card state-card-error">
                <div className="state-card-icon" aria-hidden="true">⚠</div>
                <div className="state-card-copy">
                  <strong>Activity could not be loaded.</strong>
                  <span className="error-detail">{activityErrorMessage}</span>
                  <span>Check the API connection and try again.</span>
                </div>
                <button onClick={() => activity.refetch()}>Retry</button>
              </div>
            )}
            {!activity.isPending && !activity.isError && groups.length === 0 && (
              <div className="state-card state-card-empty">
                <div className="state-card-icon" aria-hidden="true">○</div>
                <div className="state-card-copy">
                  <strong>No activity matches these filters.</strong>
                  <span>Clear a filter to broaden the ledger.</span>
                </div>
                <button onClick={() => setFilters(initialFilters)}>Clear filters</button>
              </div>
            )}
            {groups.map(([group, commits]) => (
              <section className="ledger-group" key={group} aria-label={group}>
                <h2>{group}</h2>
                {commits.map((commit) => {
                  const state = reviewState(commit)
                  const confidence = confidenceLabel(commit.attribution_confidence)
                  return (
                    <div className={`ledger-row${selected?.id === commit.id ? ' selected' : ''}`} role="row" tabIndex={0} key={commit.id} onClick={() => setSelected(commit)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); setSelected(commit) } }} aria-label={`Inspect ${commit.message}`}>
                      <span className="row-time" role="cell">{formatTime(commit.pushed_at)}</span>
                      <span className="row-change" role="cell">
                        <strong>{commit.message}</strong>
                        <code>{commit.short_sha}</code>
                        <span className="reason-chips" aria-label={`Review reasons for ${commit.short_sha}`}>
                          {buildReasonChips(commit).slice(0, 2).map((reason) => <span key={reason} className="reason-chip">{reason}</span>)}
                        </span>
                      </span>
                      <span className="row-repo" role="cell"><strong>{commit.full_name}</strong><small>{commit.branch}</small></span>
                      <span className="row-author" role="cell"><strong>{commit.author_login}</strong><small>{commit.agent_type}</small></span>
                      <span className={`confidence confidence-${confidence.toLowerCase()}`} role="cell"><i aria-hidden="true" /><span>{confidence}</span><small>{commit.attribution_confidence}</small></span>
                      <span className="row-diff mono" role="cell">+{commit.additions} −{commit.deletions}</span>
                      <span className={`review-state ${reviewStateClass(commit)}`} role="cell"><i aria-hidden="true" />{reviewState(commit)}</span>
                    </div>
                  )
                })}
              </section>
            ))}
          </div>
          {(activity.data?.has_more || cursorHistory.length > 0) && <footer className="pagination"><span>Showing {activity.data?.data.length ?? 0} changes</span><div>{cursorHistory.length > 0 && <button className="secondary-button" onClick={() => { const previous = cursorHistory[cursorHistory.length - 1] ?? null; setCursor(previous); setCursorHistory((history) => history.slice(0, -1)) }}>Previous</button>}{activity.data?.has_more && <button onClick={() => { setCursorHistory((history) => [...history, cursor]); setCursor(activity.data?.next_cursor || null) }}>Next page</button>}</div></footer>}
        </section>
        {selected && <EvidenceInspector commit={selected} onClose={() => setSelected(null)} />}
      </main>}
    </>
  )
}

export default ActivityFeed
