import { API_BASE } from '../lib/api'
export default function Settings() { return <main className="settings-page">
  <header className="page-heading"><h1>Settings</h1><p>Account, connection, and workspace details.</p></header>
  <section className="settings-section"><h2>Account</h2><dl><div><dt>Name</dt><dd>Not signed in</dd></div><div><dt>Email</dt><dd>Not signed in</dd></div></dl><p>Authentication ships with the GitHub App integration. <a href="#/login">Sign in</a></p></section>
  <section className="settings-section"><h2>GitHub connection</h2><dl><div><dt>Installation</dt><dd>No GitHub App installation on record</dd><a href="#/connect">Manage → Connect GitHub</a></div></dl></section>
  <section className="settings-section"><h2>Workspace</h2><dl><div><dt>API endpoint</dt><dd className="mono">{API_BASE}</dd></div><div><dt>Theme</dt><dd>Follows system preference</dd></div></dl></section>
  </main> }
