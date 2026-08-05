import { useQueries, useQuery } from '@tanstack/react-query'
import { fetchJson } from '../lib/api'

interface Repository {
  full_name: string
  owner: string
  name: string
  installed_at: string
  account_login: string
}
interface ReposResponse { data: Repository[] }
interface Summary { total_commits: number; ai_share_percent: number; review_needed: number }

export default function Repositories({ onView }: { onView: (repository: string) => void }) {
  const repos = useQuery<ReposResponse>({ queryKey: ['repos'], queryFn: () => fetchJson('/repos') })
  const repositories = repos.data?.data ?? []
  const summaries = useQueries({ queries: repositories.map((repository) => ({
    queryKey: ['repository-summary', repository.full_name],
    queryFn: () => fetchJson<Summary>(`/activity/summary?repository=${encodeURIComponent(repository.full_name)}`),
  })) })
  const retry = () => { void repos.refetch(); summaries.forEach((query) => void query.refetch()) }
  const failed = repos.isError || summaries.some((query) => query.isError)
  return <main className="agents-workspace">
    <div className="agents-heading"><div><h1>Repositories</h1><p>Connected repositories and the AI-authored activity within them.</p></div></div>
    <section className="repositories-ledger" aria-label="Connected repositories">
      <div className="repositories-head" aria-hidden="true"><span>Repository</span><span>Commits tracked</span><span>AI-authored share</span><span>Needs review</span></div>
      {repos.isPending && <div className="ledger-skeleton"><span /><span /><span /></div>}
      {failed && <div className="state-message" role="alert"><strong>Repositories could not be loaded.</strong><span>Check that the API is running, then try again.</span><button onClick={retry}>Retry</button></div>}
      {!repos.isPending && !failed && repositories.length === 0 && <div className="state-message" role="status"><strong>No repositories connected yet</strong><span>Install the Flagger GitHub App to start the audit trail, no CLI, no config.</span><a className="primary-button" href="#/onboarding">Connect GitHub</a></div>}
      {!failed && repositories.map((repository, index) => { const summary = summaries[index].data; return <button type="button" className="repository-row" key={repository.full_name} onClick={() => onView(repository.full_name)} aria-label={`View ${repository.full_name} activity`}>
        <strong className="mono">{repository.full_name}</strong><span>{summary?.total_commits ?? '—'}</span>
        <span className="agent-share"><span><i style={{ width: `${summary?.ai_share_percent ?? 0}%` }} /></span><small>{summary?.ai_share_percent ?? 0}%</small></span>
        {summary ? <span className={`review-state ${summary.review_needed > 0 ? 'state-needs-review' : 'state-approved'}`}><i aria-hidden="true" />{summary.review_needed ? `${summary.review_needed} need review` : 'Clear'}</span> : <span className="review-state">—</span>}
        <span className="row-action">View activity <span aria-hidden="true">→</span></span>
      </button> })}
    </section>
  </main>
}
