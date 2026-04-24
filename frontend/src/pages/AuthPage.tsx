import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';

export default function AuthPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handle = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'register') {
        await authApi.register({ username: form.username, email: form.email, password: form.password });
      }
      const data = await authApi.login({ username: form.username, password: form.password });
      // Set token in localStorage BEFORE calling /me so the interceptor can attach it
      localStorage.setItem('planner_token', data.access_token);
      const me = await authApi.me();
      setAuth(data.access_token, me);
      navigate('/');
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Error al autenticar');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center p-4">
      {/* Background texture */}
      <div className="fixed inset-0 pointer-events-none">
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              'repeating-linear-gradient(0deg, #ddd8cf 0px, #ddd8cf 1px, transparent 1px, transparent 48px), repeating-linear-gradient(90deg, #ddd8cf 0px, #ddd8cf 1px, transparent 1px, transparent 48px)',
          }}
        />
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-amber/5 rounded-full blur-[100px]" />
      </div>

      <div className="relative w-full max-w-sm animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 mb-3">
            <span className="text-2xl">📅</span>
            <h1 className="font-serif text-2xl font-medium text-ink">Planificador</h1>
          </div>
          <p className="text-ink-muted text-sm font-mono">Semana · Tareas · Revisión</p>
        </div>

        <div className="card p-8">
          {/* Mode toggle */}
          <div className="flex gap-1 mb-8 bg-surface-3 p-1 rounded-lg">
            {(['login', 'register'] as const).map((m) => (
              <button
                key={m}
                onClick={() => { setMode(m); setError(''); }}
                className={`flex-1 py-2 text-sm font-mono rounded-md transition-all ${
                  mode === m
                    ? 'bg-surface-2 text-amber shadow-sm'
                    : 'text-ink-muted hover:text-ink'
                }`}
              >
                {m === 'login' ? 'Entrar' : 'Registrarse'}
              </button>
            ))}
          </div>

          <form onSubmit={handle} className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-ink-muted mb-1.5 uppercase tracking-wider">
                Usuario
              </label>
              <input
                type="text"
                value={form.username}
                onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
                className="w-full bg-surface-3 border border-border rounded-lg px-3 py-2.5 text-sm text-ink placeholder-ink-dim focus:outline-none focus:border-amber transition-colors"
                placeholder="tu_usuario"
                required
              />
            </div>

            {mode === 'register' && (
              <div>
                <label className="block text-xs font-mono text-ink-muted mb-1.5 uppercase tracking-wider">
                  Email
                </label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  className="w-full bg-surface-3 border border-border rounded-lg px-3 py-2.5 text-sm text-ink placeholder-ink-dim focus:outline-none focus:border-amber transition-colors"
                  placeholder="tu@email.com"
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-mono text-ink-muted mb-1.5 uppercase tracking-wider">
                Contraseña
              </label>
              <input
                type="password"
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                className="w-full bg-surface-3 border border-border rounded-lg px-3 py-2.5 text-sm text-ink placeholder-ink-dim focus:outline-none focus:border-amber transition-colors"
                placeholder="••••••••"
                required
                minLength={8}
              />
            </div>

            {error && (
              <div className="text-xs font-mono text-status-discarded bg-red-950/30 border border-red-900/40 rounded-lg px-3 py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '...' : mode === 'login' ? 'Entrar' : 'Crear cuenta'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
