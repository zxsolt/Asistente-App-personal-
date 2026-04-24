import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { weeksApi } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import { useAuthStore } from '@/store/authStore';
import type { Week } from '@/types';

function fmt(d: string) {
  return new Date(d + 'T00:00:00').toLocaleDateString('es-ES', {
    day: 'numeric',
    month: 'short',
  });
}

export default function HomePage() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [creating, setCreating] = useState(false);
  const [newDates, setNewDates] = useState({ start: '', end: '' });

  const { data: weeks = [], isLoading } = useQuery<Week[]>({
    queryKey: ['weeks'],
    queryFn: weeksApi.list,
  });

  const createMutation = useMutation({
    mutationFn: (d: { start_date: string; end_date: string }) => weeksApi.create(d),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weeks'] });
      setCreating(false);
      setNewDates({ start: '', end: '' });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => weeksApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['weeks'] }),
  });

  return (
    <div className="min-h-screen bg-canvas">
      {/* Background */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.025]"
        style={{
          backgroundImage:
            'repeating-linear-gradient(0deg, #ddd8cf 0px, #ddd8cf 1px, transparent 1px, transparent 48px), repeating-linear-gradient(90deg, #ddd8cf 0px, #ddd8cf 1px, transparent 1px, transparent 48px)',
        }}
      />

      {/* Header */}
      <header className="sticky top-0 z-10 bg-canvas/80 backdrop-blur-md border-b border-border">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">📅</span>
            <span className="font-serif text-lg font-medium text-ink">Planificador</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs font-mono text-ink-dim hidden sm:block">
              {user?.username}
            </span>
            <button onClick={logout} className="btn-ghost text-xs">
              Salir
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-12 animate-fade-in">
        {/* Page title */}
        <div className="flex items-end justify-between mb-10">
          <div>
            <p className="section-title mb-1">tus semanas</p>
            <h2 className="font-serif text-3xl font-medium text-ink">
              Semanas de trabajo
            </h2>
          </div>
          <button
            onClick={() => setCreating(true)}
            className="btn-primary flex items-center gap-2"
          >
            <span>+</span>
            <span>Nueva semana</span>
          </button>
        </div>

        {/* Create form */}
        {creating && (
          <div className="card p-6 mb-6 border-amber/30 animate-slide-down">
            <p className="section-title">nueva semana</p>
            <div className="grid grid-cols-2 gap-4 mb-4">
              {[
                { label: 'Inicio', key: 'start' as const },
                { label: 'Fin', key: 'end' as const },
              ].map(({ label, key }) => (
                <div key={key}>
                  <label className="block text-xs font-mono text-ink-muted mb-1.5">{label}</label>
                  <input
                    type="date"
                    value={newDates[key]}
                    onChange={(e) => setNewDates((d) => ({ ...d, [key]: e.target.value }))}
                    className="w-full bg-surface-3 border border-border rounded px-3 py-2 text-sm text-ink focus:outline-none focus:border-amber transition-colors"
                  />
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() =>
                  createMutation.mutate({ start_date: newDates.start, end_date: newDates.end })
                }
                disabled={!newDates.start || !newDates.end || createMutation.isPending}
                className="btn-primary disabled:opacity-50"
              >
                Crear
              </button>
              <button onClick={() => setCreating(false)} className="btn-ghost">
                Cancelar
              </button>
            </div>
          </div>
        )}

        {/* Week list */}
        {isLoading ? (
          <div className="text-center py-20 text-ink-dim font-mono text-sm">Cargando…</div>
        ) : weeks.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-5xl mb-4 opacity-30">📋</div>
            <p className="font-mono text-ink-dim">No hay semanas todavía.</p>
            <p className="font-mono text-ink-dim text-sm mt-1">Crea la primera para empezar.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {weeks.map((w) => (
              <WeekCard
                key={w.id}
                week={w}
                onClick={() => navigate(`/week/${w.id}`)}
                onDelete={(e) => {
                  e.stopPropagation();
                  if (confirm('¿Eliminar esta semana y todos sus datos?'))
                    deleteMutation.mutate(w.id);
                }}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function WeekCard({ week, onClick, onDelete }: { week: Week; onClick: () => void; onDelete: (e: React.MouseEvent) => void }) {
  const start = fmt(week.start_date);
  const end = fmt(week.end_date);

  return (
    <button
      onClick={onClick}
      className="card p-5 text-left group hover:border-border-2 hover:bg-surface-2 transition-all cursor-pointer relative"
    >
      <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={onDelete}
          className="w-6 h-6 flex items-center justify-center rounded text-ink-dim hover:text-status-discarded hover:bg-red-950/40 transition-all text-xs"
        >
          ×
        </button>
      </div>
      <p className="section-title mb-2">semana</p>
      <p className="font-serif text-lg text-ink mb-1">
        {start} — {end}
      </p>
      <p className="text-xs font-mono text-ink-dim">
        {new Date(week.start_date + 'T00:00:00').toLocaleDateString('es-ES', {
          year: 'numeric',
          month: 'long',
        })}
      </p>
      <div className="mt-4 flex items-center gap-1 text-xs font-mono text-amber opacity-0 group-hover:opacity-100 transition-opacity">
        <span>Abrir</span>
        <span>→</span>
      </div>
    </button>
  );
}
