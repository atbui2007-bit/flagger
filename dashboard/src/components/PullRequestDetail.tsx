import { useQuery } from '@tanstack/react-query'
import { fetchJson, relativeDate } from '../lib/api'

interface PullRequest { title: string; github_pr_number: number; url: string; author_login: string; state: string; head_branch: string; merged_at?: string | null; created_at: string; updated_at: string; closed_at?: string | null }
interface Commit { id?: string; sha: string; short_sha?: string; message: string; url: string; author_login?: string; agent_type?: string; additions?: number; deletions?: number; risk_no_review?: boolean; risk_level?: string | null }
interface CiRun { workflow_name: string; status: string; conclusion?: string | null; started_at?: string | null; completed_at?: string | null }
interface Review { reviewer_login: string; state: string; submitted_at: string }
interface Response { pull_request: PullRequest; commits: Commit[]; ci_runs: CiRun[]; reviews: Review[] }

function Pill({ kind = 'neutral', children }: { kind?: 'neutral' | 'needs-review' | 'reviewed' | 'approved'; children: React.ReactNode }) {
  return <span className={kind === 'neutral' ? 'neutral-pill' : `review-state state-${kind}`}><i aria-hidden="true" />{children}</span>
}
function duration(start?: string | null, end?: string | null) { if (!start || !end) return ''; const seconds = Math.max(0, Math.round((new Date(end).getTime() - new Date(start).getTime()) / 1000)); return seconds < 60 ? `${seconds}s` : `${Math.round(seconds / 60)}m` }

export default function PullRequestDetail({ owner, name, number }: { owner: string; name: string; number: string }) {
  const query = useQuery<Response>({ queryKey: ['pull-request', owner, name, number], queryFn: () => fetchJson(`/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/prs/${encodeURIComponent(number)}`) })
  if (query.isPending) return <main className="pr-page"><div className="ledger-skeleton"><span /><span /><span /><span /></div></main>
  if (query.isError) return <main className="pr-page"><div className="state-message"><strong>Pull request not found or not yet ingested</strong><a href="#/repositories">Back to repositories</a></div></main>
  const { pull_request: pr, commits, ci_runs: checks, reviews } = query.data
  const merged = Boolean(pr.merged_at) || pr.state.toLowerCase() === 'merged'
  return <main className="pr-page">
    <div className="breadcrumb"><a className="mono" href="#/repositories">{owner}/{name}</a><span>#{number}</span></div>
    <header className="pr-heading"><div><h1>{pr.title}</h1><p>Opened by {pr.author_login} on <code>{pr.head_branch}</code> · {relativeDate(pr.created_at)} · updated {relativeDate(pr.updated_at)}</p></div><Pill kind={merged ? 'reviewed' : 'neutral'}>{merged ? 'Merged' : pr.state.toLowerCase() === 'open' ? 'Open' : 'Closed'}</Pill></header>
    <section className="pr-section"><h2>Commits <span>{commits.length}</span></h2>{commits.length === 0 && <p className="section-empty">No commits recorded for this pull request.</p>}
      {commits.map((commit) => { const state = commit.risk_no_review ? 'needs-review' : commit.risk_level === 'low' ? 'approved' : 'reviewed'; return <a className="pr-commit-row" href={commit.url} target="_blank" rel="noreferrer" key={commit.id ?? commit.sha}><span className="row-change"><strong>{commit.message}</strong><code>{commit.short_sha ?? commit.sha.slice(0, 7)}</code></span><span>{commit.author_login ?? commit.agent_type ?? 'Unknown author'}</span><span className="mono">+{commit.additions ?? 0} −{commit.deletions ?? 0}</span><Pill kind={state}>{state === 'needs-review' ? 'Needs review' : state === 'approved' ? 'Approved' : 'Reviewed'}</Pill></a> })}
    </section>
    <section className="pr-section"><h2>Checks <span>{checks.length}</span></h2>{checks.length === 0 && <p className="section-empty">No checks recorded for this pull request.</p>}
      {checks.map((check, index) => { const result = check.conclusion?.toLowerCase(); const kind = result === 'success' ? 'approved' : result === 'failure' ? 'needs-review' : 'neutral'; return <div className="check-row" key={`${check.workflow_name}-${index}`}><strong>{check.workflow_name}</strong><Pill kind={kind}>{result === 'success' ? 'Passed' : result === 'failure' ? 'Failed' : check.status}</Pill><span>{relativeDate(check.started_at)}</span><span>{duration(check.started_at, check.completed_at)}</span></div> })}
    </section>
    <section className="pr-section"><h2>Reviews <span>{reviews.length}</span></h2>{reviews.length === 0 && <p className="section-empty">No reviews recorded for this pull request.</p>}
      {reviews.map((review, index) => { const state = review.state.toLowerCase(); const kind = state === 'approved' ? 'approved' : state === 'changes_requested' ? 'needs-review' : 'reviewed'; return <div className="review-row" key={`${review.reviewer_login}-${index}`}><strong>{review.reviewer_login}</strong><Pill kind={kind}>{state === 'approved' ? 'Approved' : state === 'changes_requested' ? 'Changes requested' : 'Commented'}</Pill><span>{relativeDate(review.submitted_at)}</span></div> })}
    </section>
    <footer className="pr-footer"><a href={pr.url} target="_blank" rel="noreferrer">View on GitHub <span aria-hidden="true">↗</span></a></footer>
  </main>
}
