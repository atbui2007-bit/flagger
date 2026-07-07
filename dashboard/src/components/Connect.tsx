import { useQuery } from '@tanstack/react-query'
import { fetchJson } from '../lib/api'

interface Facets { repositories: string[] }
const steps = [
  ['Install the GitHub App and choose repositories', 'Select only the organizations and repositories you want Flagger to observe.'],
  ['Flagger receives webhooks and attributes each commit', 'Activity begins flowing without wrappers or developer configuration.'],
  ['Review the ledger with honest confidence labels', 'Direct provenance and suspected attribution remain explicitly separate.'],
]
export default function Connect() {
  const facets = useQuery<Facets>({ queryKey: ['activity-facets'], queryFn: () => fetchJson('/activity/facets') })
  return <main className="page-narrow connect-page">
    <header className="page-heading"><h1>Connect GitHub</h1><p>Install the Flagger GitHub App once per organization. Activity starts flowing immediately, no CLI wrappers, no per-developer setup.</p></header>
    <ol className="connect-steps">{steps.map(([title, copy], index) => <li key={title}><span>{index + 1}</span><div><strong>{title}</strong><p>{copy}</p></div></li>)}</ol>
    <div className="connect-actions"><a className="primary-button" href="https://github.com/apps" title="App slug pending">Install GitHub App</a><a href="#/repositories">Already installed it <span aria-hidden="true">→</span></a></div>
    <section className="flat-section"><h2>Repositories reporting activity</h2>
      {facets.isPending && <div className="ledger-skeleton"><span /><span /></div>}
      {facets.data?.repositories.map((repository) => <div className="reporting-row" key={repository}><code>{repository}</code><span>Receiving webhooks</span></div>)}
      {!facets.isPending && !facets.data?.repositories.length && <p className="quiet-copy">No repositories are reporting yet. Installation typically takes under a minute to appear.</p>}
    </section>
  </main>
}
