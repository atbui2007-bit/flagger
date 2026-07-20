import { useQuery } from '@tanstack/react-query'
import { API_BASE, fetchJson, GIT_AI_URL, relativeDate } from '../lib/api'
import { supabase } from '../lib/supabase'
import { getProviderToken, useSession } from '../lib/auth'

interface Installation {
  github_installation_id: number
  account_login: string
  account_type: string | null
  installed_at: string
  suspended_at: string | null
  repo_count: number
}

export default function Settings() {
  const auth = useSession()
  const installations = useQuery<{ data: Installation[] }>({
    queryKey: ['installations'],
    queryFn: () => fetchJson('/installations'),
    enabled: auth.status === 'signed-in' || auth.status === 'disabled',
  })
  const user = auth.status === 'signed-in' ? auth.session.user : null
  const githubLogin = (user?.user_metadata?.user_name ?? user?.user_metadata?.preferred_username) as string | undefined
  const reconnect = () => {
    if (!supabase) return
    void supabase.auth.signInWithOAuth({
      provider: 'github',
      options: { redirectTo: location.origin, scopes: 'read:user' },
    })
  }
  return <main className="settings-page">
  <header className="page-heading"><h1>Settings</h1><p>Account, connection, and workspace details.</p></header>
  <section className="settings-section"><h2>Account</h2>
    {user ? <>
      <dl><div><dt>GitHub</dt><dd>{githubLogin ?? 'Unknown'}</dd></div><div><dt>Email</dt><dd>{user.email ?? 'Not provided'}</dd></div></dl>
      <div className="settings-actions"><button type="button" className="ghost-button" onClick={() => { if (supabase) void supabase.auth.signOut() }}>Sign out</button></div>
    </> : <>
      <dl><div><dt>GitHub</dt><dd>Not signed in</dd></div><div><dt>Email</dt><dd>Not signed in</dd></div></dl>
      <p>Sign in with GitHub to see your account and connection details. <a href="#/login">Sign in</a></p>
    </>}
  </section>
  <section className="settings-section"><h2>GitHub connection</h2>
    {installations.isPending && <div className="ledger-skeleton"><span /></div>}
    {installations.isError && <p className="quiet-copy">Couldn't load installations — sign in and try again.</p>}
    {installations.data && (installations.data.data.length ? <dl>{installations.data.data.map((installation) => <div key={installation.github_installation_id}>
      <dt>{installation.account_login}</dt>
      <dd>{installation.suspended_at ? 'Suspended' : `${installation.repo_count} ${installation.repo_count === 1 ? 'repository' : 'repositories'} · installed ${relativeDate(installation.installed_at)}`}</dd>
    </div>)}</dl> : <dl><div><dt>Installation</dt><dd>No GitHub App installation on record</dd></div></dl>)}
    <div className="settings-actions"><a href="#/connect">Manage installations <span aria-hidden="true">→</span></a></div>
    {user && !getProviderToken() && <div className="settings-actions">
      <button type="button" className="ghost-button" onClick={reconnect}>Reconnect GitHub</button>
      <p className="quiet-copy">Your GitHub session has expired, so repository access can't refresh. Reconnecting restores it.</p>
    </div>}
  </section>
  <section className="settings-section"><h2>Attribution</h2>
    <p className="quiet-copy">Flagger reads git-ai notes when a repo has them, upgrading attribution from suspected heuristics to certain, line-level provenance. git-ai is free, open source, and installs in one line per developer — no account required.</p>
    <div className="settings-actions"><a href={GIT_AI_URL} target="_blank" rel="noreferrer">Get git-ai on GitHub <span aria-hidden="true">↗</span></a></div>
  </section>
  <section className="settings-section"><h2>Workspace</h2><dl><div><dt>API endpoint</dt><dd className="mono">{API_BASE}</dd></div><div><dt>Theme</dt><dd>Set with the sidebar toggle</dd></div></dl></section>
  </main>
}
