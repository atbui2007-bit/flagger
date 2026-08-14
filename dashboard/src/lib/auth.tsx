import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import type { Session } from '@supabase/supabase-js'
import { supabase } from './supabase'

const PROVIDER_TOKEN_KEY = 'flagger:provider_token'
const PENDING_INSTALL_KEY = 'flagger:pending_installation'

// The provider token lives in localStorage, not sessionStorage: Supabase only
// hands it over in the instant after the OAuth redirect, and access grants are
// renewed by /installations/sync-access, which needs it. Per-tab storage meant
// every reopened tab silently skipped the sync until grants expired and the user
// had to reconnect GitHub by hand. Cleared on sign-out and when GitHub rejects it.
export const getProviderToken = () => localStorage.getItem(PROVIDER_TOKEN_KEY)
export const clearProviderToken = () => localStorage.removeItem(PROVIDER_TOKEN_KEY)
export const getPendingInstallation = () => sessionStorage.getItem(PENDING_INSTALL_KEY)
export const setPendingInstallation = (id: string) => sessionStorage.setItem(PENDING_INSTALL_KEY, id)
export const clearPendingInstallation = () => sessionStorage.removeItem(PENDING_INSTALL_KEY)

export type AuthState =
  | { status: 'disabled' }
  | { status: 'loading' }
  | { status: 'signed-out' }
  | { status: 'signed-in'; session: Session }

const AuthContext = createContext<AuthState>({ status: 'disabled' })
export const useSession = () => useContext(AuthContext)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(supabase ? { status: 'loading' } : { status: 'disabled' })
  useEffect(() => {
    if (!supabase) return
    void supabase.auth.getSession().then(({ data }) =>
      setState(data.session ? { status: 'signed-in', session: data.session } : { status: 'signed-out' }))
    const { data: sub } = supabase.auth.onAuthStateChange((event, session) => {
      // provider_token (the GitHub OAuth token) only exists in the session
      // immediately after the OAuth redirect; supabase-js does not persist it.
      // Stash it for the installation claim flow.
      if (session?.provider_token) localStorage.setItem(PROVIDER_TOKEN_KEY, session.provider_token)
      if (event === 'SIGNED_OUT') localStorage.removeItem(PROVIDER_TOKEN_KEY)
      setState(session ? { status: 'signed-in', session } : { status: 'signed-out' })
    })
    return () => sub.subscription.unsubscribe()
  }, [])
  return <AuthContext.Provider value={state}>{children}</AuthContext.Provider>
}
