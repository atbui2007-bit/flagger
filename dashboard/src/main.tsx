import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App.tsx'
import { AuthProvider, setPendingInstallation } from './lib/auth'

// GitHub App Setup URL redirect lands with ?installation_id=...&setup_action=install
// in the query string (before the hash). Capture it before React renders, then strip
// only those params -- a Supabase ?code= param must survive untouched.
const params = new URLSearchParams(location.search)
const installationId = params.get('installation_id')
if (installationId && params.get('setup_action') === 'install') {
  setPendingInstallation(installationId)
}
if (params.has('installation_id') || params.has('setup_action')) {
  params.delete('installation_id')
  params.delete('setup_action')
  const query = params.toString()
  history.replaceState(null, '', location.pathname + (query ? `?${query}` : '') + location.hash)
} else if (location.hash.includes('?')) {
  // GitHub appends its params after the Setup URL verbatim -- if that URL ever
  // points at a hash route (e.g. /#/connect), they land inside the hash instead.
  const [hashPath, hashQuery] = location.hash.split('?')
  const hashParams = new URLSearchParams(hashQuery)
  const hashInstallationId = hashParams.get('installation_id')
  if (hashInstallationId && hashParams.get('setup_action') === 'install') {
    setPendingInstallation(hashInstallationId)
    hashParams.delete('installation_id')
    hashParams.delete('setup_action')
    const rest = hashParams.toString()
    history.replaceState(null, '', location.pathname + location.search + hashPath + (rest ? `?${rest}` : ''))
  }
}

const queryClient = new QueryClient()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
)
