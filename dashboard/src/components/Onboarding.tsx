import { useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchJson } from '../lib/api'
import { supabase } from '../lib/supabase'
import { clearPendingInstallation, getPendingInstallation, getProviderToken, useSession } from '../lib/auth'

const defaultInstallUrl = 'https://github.com/apps'

function githubLogin(auth: ReturnType<typeof useSession>) {
  if (auth.status !== 'signed-in') return 'GitHub'
  const metadata = auth.session.user.user_metadata
  return metadata.user_name || metadata.preferred_username || metadata.name || auth.session.user.email || 'GitHub'
}

function isTokenError(message: string) {
  const normalized = message.toLowerCase()
  return normalized.includes('github token') || normalized.includes('expired') || normalized.includes('revoked') || normalized.includes('bad credentials')
}

export default function Onboarding() {
  const auth = useSession()
  const queryClient = useQueryClient()
  const installUrl = import.meta.env.VITE_GITHUB_APP_INSTALL_URL ?? defaultInstallUrl
  const pending = getPendingInstallation()
  const login = githubLogin(auth)
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
      void queryClient.invalidateQueries({ queryKey: ['repos'] })
      void queryClient.invalidateQueries({ queryKey: ['repository-summary'] })
    },
  })

  useEffect(() => {
    if (!pending || auth.status !== 'signed-in' || claim.status !== 'idle') return
    const token = getProviderToken()
    if (token) claim.mutate({ installationId: pending, providerToken: token })
  }, [pending, auth.status, claim])

  const reauthenticate = () => {
    if (!supabase) return
    void supabase.auth.signInWithOAuth({
      provider: 'github',
      options: { redirectTo: location.origin, scopes: 'read:user' },
    })
  }
  const signOut = () => {
    if (supabase) void supabase.auth.signOut()
  }
  const retryClaim = () => {
    const token = getProviderToken()
    if (pending && token) claim.mutate({ installationId: pending, providerToken: token })
  }
  const errorMessage = claim.error instanceof Error ? claim.error.message : 'Could not link the installation.'
  const needsReauth = Boolean(pending) && auth.status === 'signed-in' && (!getProviderToken() || (claim.isError && isTokenError(errorMessage)))

  return <main className="onboarding-page">
    <section className="onboarding-panel" aria-labelledby="onboarding-title">
      <a className="login-brand" href="#/">Flagger</a>
      <header className="page-heading">
        <h1 id="onboarding-title">Connect your first repository</h1>
        <p>Install the GitHub App, choose repositories, and Flagger will start the audit trail on the next push.</p>
      </header>
      <ol className="connect-steps">
        <li data-state="done"><span>1</span><div><strong>Signed in as {login}</strong><p>Your GitHub identity is ready for the installation claim.</p></div></li>
        <li data-state={claim.isSuccess ? 'done' : 'active'}><span>2</span><div><strong>Install the Flagger GitHub App</strong><p>Select the organizations and repositories you want Flagger to observe.</p></div></li>
        <li data-state={claim.isSuccess ? 'active' : 'pending'}><span>3</span><div><strong>Your ledger fills in</strong><p>Repositories appear immediately. Activity appears after the next push.</p></div></li>
      </ol>
      {claim.isPending && <p className="quiet-copy" role="status">Linking your installation…</p>}
      {claim.isSuccess && <p className="quiet-copy" role="status">Connected <strong>{claim.data.account_login}</strong>. Activity will appear as webhooks arrive.</p>}
      {needsReauth && <div className="connect-claim-error" role="alert">
        <p>Your GitHub token expired or was revoked before the installation could be linked.</p>
        <button type="button" className="primary-button" onClick={reauthenticate}>Re-authenticate with GitHub</button>
      </div>}
      {claim.isError && !needsReauth && <div className="connect-claim-error" role="alert">
        <p>Could not link the installation: {errorMessage}.</p>
        <button type="button" className="primary-button" onClick={retryClaim}>Retry</button>
      </div>}
      <div className="connect-actions">
        <a className="primary-button" href={installUrl} title={installUrl === defaultInstallUrl ? 'App slug pending' : undefined}>Install GitHub App</a>
      </div>
      <footer className="onboarding-footer">Signed in as {login} <span aria-hidden="true">·</span> <button type="button" onClick={signOut}>Sign out</button></footer>
    </section>
  </main>
}
