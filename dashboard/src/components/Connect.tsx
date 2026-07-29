import { useQuery } from '@tanstack/react-query'
import { fetchJson, relativeDate } from '../lib/api'
import { useSession } from '../lib/auth'

interface Repository {
  full_name: string
  owner: string
  name: string
  installed_at: string
  account_login: string
}
interface Installation {
  github_installation_id: number
  account_login: string
  account_type: string | null
  installed_at: string
  suspended_at: string | null
  deleted_at: string | null
  repo_count: number
}
const defaultInstallUrl = 'https://github.com/apps'

export default function Connect() {
  const auth = useSession()
  const repos = useQuery<{ data: Repository[] }>({ queryKey: ['repos'], queryFn: () => fetchJson('/repos') })
  const installations = useQuery<{ data: Installation[] }>({
    queryKey: ['installations'],
    queryFn: () => fetchJson('/installations'),
    enabled: auth.status === 'signed-in' || auth.status === 'disabled',
  })
  const installUrl = import.meta.env.VITE_GITHUB_APP_INSTALL_URL ?? defaultInstallUrl

  return <main className="page-narrow connect-page">
    <header className="page-heading"><h1>Connect GitHub</h1><p>Install the Flagger GitHub App once per organization. Activity starts flowing immediately, no CLI wrappers, no per-developer setup.</p></header>
    <div className="connect-actions"><a className="primary-button" href={installUrl} title={installUrl === defaultInstallUrl ? 'App slug pending' : undefined}>Install another GitHub App installation</a><a href="#/repositories">View repositories <span aria-hidden="true">→</span></a></div>
    {installations.data && installations.data.data.length > 0 && <section className="flat-section"><h2>Connected installations</h2>
      {installations.data.data.map((installation) => <div className="reporting-row" key={installation.github_installation_id}>
        <code>{installation.account_login}</code>
        <span>{installation.suspended_at ? 'Suspended' : `${installation.repo_count} ${installation.repo_count === 1 ? 'repository' : 'repositories'} · installed ${relativeDate(installation.installed_at)}`}</span>
      </div>)}
    </section>}
    <section className="flat-section"><h2>Repositories connected</h2>
      {repos.isPending && <div className="ledger-skeleton"><span /><span /></div>}
      {repos.data?.data.map((repository) => <div className="reporting-row" key={repository.full_name}><code>{repository.full_name}</code><span>Installed for {repository.account_login} {relativeDate(repository.installed_at)}</span></div>)}
      {repos.isError && <p className="quiet-copy">Couldn't load repositories — sign in and try again.</p>}
      {!repos.isPending && !repos.isError && !repos.data?.data.length && <p className="quiet-copy">No repositories connected yet. Install the GitHub App to choose repositories.</p>}
    </section>
  </main>
}
