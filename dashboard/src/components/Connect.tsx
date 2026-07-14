import { useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchJson, relativeDate } from '../lib/api'
import { supabase } from '../lib/supabase'
import { useSession, getPendingInstallation, clearPendingInstallation, getProviderToken } from '../lib/auth'

interface Facets { repositories: string[] }
interface Installation {
  github_installation_id: number
  account_login: string
  account_type: string | null
  installed_at: string
  suspended_at: string | null
  deleted_at: string | null
  repo_count: number
}
const steps = [
  ['Install the GitHub App and choose repositories', 'Select only the organizations and repositories you want Flagger to observe.'],
  ['Flagger receives webhooks and attributes each commit', 'Activity begins flowing without wrappers or developer configuration.'],
  ['Review the ledger with honest confidence labels', 'Direct provenance and suspected attribution remain explicitly separate.'],
]
const defaultInstallUrl = 'https://github.com/apps'

export default function Connect() {
  const auth = useSession()
  const queryClient = useQueryClient()
  const facets = useQuery<Facets>({ queryKey: ['activity-facets'], queryFn: () => fetchJson('/activity/facets') })
  const installations = useQuery<{ data: Installation[] }>({
    queryKey: ['installations'],
    queryFn: () => fetchJson('/installations'),
    enabled: auth.status === 'signed-in' || auth.status === 'disabled',
  })
  const installUrl = import.meta.env.VITE_GITHUB_APP_INSTALL_URL ?? defaultInstallUrl

  const pending = getPendingInstallation()
  const claim = useMutation({
    mutationFn: (vars: { installationId: string; providerToken: string }) =>
      fetchJson<{ status: string; installation_id: number; account_login: string }>('/installations/claim', {
        method: 'POST',
        json: { installation_id: Number(vars.installationId), provider_token: vars.providerToken },
      }),
    onSuccess: () => {
      clearPendingInstallation()
      void queryClient.invalidateQueries({ queryKey: ['installations'] })
      void queryClient.invalidateQueries({ queryKey: ['activity-facets'] })
      void queryClient.invalidateQueries({ queryKey: ['activity'] })
    },
  })
  const needsReauth = Boolean(pending) && auth.status === 'signed-in' && !getProviderToken()
  useEffect(() => {
    if (!pending || auth.status !== 'signed-in' || claim.status !== 'idle') return
    const token = getProviderToken()
    if (token) claim.mutate({ installationId: pending, providerToken: token })
    // No token (page refreshed after install): the re-auth CTA below handles it.
  }, [pending, auth.status, claim])

  const reauthenticate = () => {
    if (!supabase) return
    void supabase.auth.signInWithOAuth({
      provider: 'github',
      options: { redirectTo: location.origin, scopes: 'read:user' },
    })
  }

  return <main className="page-narrow connect-page">
    <header className="page-heading"><h1>Connect GitHub</h1><p>Install the Flagger GitHub App once per organization. Activity starts flowing immediately, no CLI wrappers, no per-developer setup.</p></header>
    {claim.isPending && <p className="quiet-copy" role="status">Linking your installation…</p>}
    {claim.isSuccess && <p className="quiet-copy" role="status">Connected <strong>{claim.data.account_login}</strong>. Activity will appear as webhooks arrive.</p>}
    {claim.isError && <div className="connect-claim-error" role="alert">
      <p>Could not link the installation: {claim.error instanceof Error ? claim.error.message : 'unknown error'}.</p>
      <button type="button" className="primary-button" onClick={() => { const token = getProviderToken(); if (pending && token) claim.mutate({ installationId: pending, providerToken: token }) }}>Retry</button>
    </div>}
    {needsReauth && <div className="connect-claim-error" role="alert">
      <p>Your GitHub session expired before the installation could be linked.</p>
      <button type="button" className="primary-button" onClick={reauthenticate}>Re-authenticate with GitHub to finish connecting</button>
    </div>}
    <ol className="connect-steps">{steps.map(([title, copy], index) => <li key={title}><span>{index + 1}</span><div><strong>{title}</strong><p>{copy}</p></div></li>)}</ol>
    <div className="connect-actions"><a className="primary-button" href={installUrl} title={installUrl === defaultInstallUrl ? 'App slug pending' : undefined}>Install GitHub App</a><a href="#/repositories">Already installed it <span aria-hidden="true">→</span></a></div>
    {installations.data && installations.data.data.length > 0 && <section className="flat-section"><h2>Connected installations</h2>
      {installations.data.data.map((installation) => <div className="reporting-row" key={installation.github_installation_id}>
        <code>{installation.account_login}</code>
        <span>{installation.suspended_at ? 'Suspended' : `${installation.repo_count} ${installation.repo_count === 1 ? 'repository' : 'repositories'} · installed ${relativeDate(installation.installed_at)}`}</span>
      </div>)}
    </section>}
    <section className="flat-section"><h2>Repositories reporting activity</h2>
      {facets.isPending && <div className="ledger-skeleton"><span /><span /></div>}
      {facets.data?.repositories.map((repository) => <div className="reporting-row" key={repository}><code>{repository}</code><span>Receiving webhooks</span></div>)}
      {!facets.isPending && !facets.data?.repositories.length && <p className="quiet-copy">No repositories are reporting yet. Installation typically takes under a minute to appear.</p>}
    </section>
  </main>
}
