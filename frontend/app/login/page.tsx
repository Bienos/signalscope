'use client';

import {useRouter} from 'next/navigation';
import {FormEvent, useState} from 'react';

export default function LoginPage() {
  const router = useRouter();
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage('');
    const form = new FormData(event.currentTarget);
    const response = await fetch('/api/session/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        username: form.get('email'),
        password: form.get('password'),
      }),
    });
    if (response.ok) {
      router.push('/dashboard');
      router.refresh();
      return;
    }
    const payload = await response.json().catch(() => ({detail: 'Sign-in failed'})) as {detail?: string};
    setMessage(payload.detail || 'Sign-in failed');
    setBusy(false);
  }

  async function signOut() {
    setBusy(true);
    await fetch('/api/session/logout', {method: 'POST'});
    setMessage('Signed out. Demo fixtures remain viewable only when demo mode is enabled.');
    setBusy(false);
    router.refresh();
  }

  return <main id="main-content" className="loginpage">
    <form className="panel loginpanel" onSubmit={submit}>
      <div className="eyebrow">Secure workspace session</div>
      <h1>Sign in to SignalScope</h1>
      <p>Demo evidence can be viewed without a session when demo mode is explicitly enabled. Sign in before saving decisions, notes, briefs or reports.</p>
      <label>Email<input name="email" type="email" autoComplete="username" required/></label>
      <label>Password<input name="password" type="password" autoComplete="current-password" required/></label>
      <button className="action" disabled={busy} type="submit">{busy ? 'Signing in…' : 'Sign in'}</button>
      <button className="action secondary" disabled={busy} type="button" onClick={signOut}>Sign out of this browser</button>
      {message && <p role="alert" className="limitation">{message}</p>}
    </form>
  </main>;
}
