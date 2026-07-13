import { useQueries, useQuery } from '@tanstack/react-query'
import { fetchJson } from '../lib/api'

interface Facets { repositories: string[] }
interface Summary { total_commits: number; ai_share_percent: number; review_needed: number }

export default function Repositories({ onView }: { onView: (repository: string) => void }) {
  const facets = useQuery<Facets>({ queryKey: ['activity-facets'], queryFn: () => fetchJson('/activity/facets') })
  const repositories = facets.data?.repositories ?? []
  const summaries = useQueries({ queries: repositories.map((repository) => ({
    queryKey: ['repository-summary', repository],
    queryFn: () => fetchJson<Summary>(`/activity/summary?repository=${encodeURIComponent(repository)}`),
  })) })
  const retry = () => { void facets.refetch(); summaries.forEach((query) => void query.refetch()) }
  const failed = facets.isError || summaries.some((query) => query.isError)
  return <main className="agents-workspace">
    <div className="agents-heading"><div><h1>Repositories</h1><p>Connected repositories and the AI-authored activity within them.</p></div></div>
    <div className="repositories-ledger" role="table" aria-label="Connected repositories">
      <div className="repositories-head" role="row"><span role="columnheader">Repository</span><span role="columnheader">Commits tracked</span><span role="columnheader">AI-authored share</span><span role="columnheader">Needs review</span><span role="columnheader" className="sr-only">Action</span></div>
      {facets.isPending && <div className="ledger-skeleton"><span /><span /><span /></div>}
      {failed && <div className="state-message"><strong>Repositories could not be loaded.</strong><span>Check that the API is running, then try again.</span><button onClick={retry}>Retry</button></div>}
      {!facets.isPending && !failed && repositories.length === 0 && <div className="state-message"><strong>No repositories connected yet</strong><span>Install the Flagger GitHub App to start the audit trail, no CLI, no config.</span><a className="primary-button" href="#/connect">Connect GitHub</a></div>}
      {!failed && repositories.map((repository, index) => { const summary = summaries[index].data; return <button className="repository-row" role="row" key={repository} onClick={() => onView(repository)} aria-label={`View ${repository} activity`}>
        <strong className="mono" role="cell">{repository}</strong><span role="cell">{summary?.total_commits ?? '—'}</span>
        <span className="agent-share" role="cell"><span><i style={{ width: `${summary?.ai_share_percent ?? 0}%` }} /></span><small>{summary?.ai_share_percent ?? 0}%</small></span>
        {summary ? <span className={`review-state ${summary.review_needed > 0 ? 'state-needs-review' : 'state-approved'}`} role="cell"><i aria-hidden="true" />{summary.review_needed ? `${summary.review_needed} need review` : 'Clear'}</span> : <span className="review-state" role="cell">—</span>}
        <span className="row-action" role="cell">View activity <span aria-hidden="true">→</span></span>
      </button> })}
    </div>
  </main>
}
