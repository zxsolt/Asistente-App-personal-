import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { reviewApi } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import type { WeekDetail } from '@/types';

interface Props { week: WeekDetail }

const FIELDS = [
  {
    key: 'closed_this_week' as const,
    icon: '✅',
    label: '¿Qué cerré esta semana?',
    placeholder: 'Describe los hitos o tareas que completaste…',
  },
  {
    key: 'pending_why' as const,
    icon: '⏳',
    label: '¿Qué queda pendiente y por qué?',
    placeholder: 'Lista lo que no cerraste y el motivo…',
  },
  {
    key: 'moving_to_next_week' as const,
    icon: '➡️',
    label: '¿Qué muevo a la semana que viene?',
    placeholder: 'Lo que trasladas a la próxima semana…',
  },
];

export default function ReviewSection({ week }: Props) {
  const wid = week.id;
  const rv = week.weekly_review;
  const [form, setForm] = useState({
    closed_this_week:     rv?.closed_this_week     ?? '',
    pending_why:          rv?.pending_why          ?? '',
    moving_to_next_week:  rv?.moving_to_next_week  ?? '',
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setForm({
      closed_this_week:    week.weekly_review?.closed_this_week    ?? '',
      pending_why:         week.weekly_review?.pending_why         ?? '',
      moving_to_next_week: week.weekly_review?.moving_to_next_week ?? '',
    });
  }, [week.id, week.weekly_review]);

  const saveMut = useMutation({
    mutationFn: () =>
      reviewApi.upsert(wid, {
        closed_this_week:     form.closed_this_week    || null,
        pending_why:          form.pending_why         || null,
        moving_to_next_week:  form.moving_to_next_week || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['week', wid] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  return (
    <div className="animate-fade-in">
      <div className="flex items-end justify-between mb-6">
        <div>
          <p className="section-title mb-1">🔁 revisión</p>
          <h2 className="font-serif text-2xl font-medium text-ink">Revisión semanal</h2>
        </div>
        <div className="flex items-center gap-3">
          {saved && (
            <span className="text-xs font-mono text-status-done animate-fade-in">✓ Guardado</span>
          )}
          <button
            onClick={() => saveMut.mutate()}
            disabled={saveMut.isPending}
            className="btn-primary disabled:opacity-50"
          >
            Guardar
          </button>
        </div>
      </div>

      <div className="space-y-5">
        {FIELDS.map((f) => (
          <div key={f.key} className="card p-5">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-base">{f.icon}</span>
              <h3 className="font-serif text-base font-medium text-ink">{f.label}</h3>
            </div>
            <textarea
              value={form[f.key]}
              onChange={(e) => setForm((p) => ({ ...p, [f.key]: e.target.value }))}
              placeholder={f.placeholder}
              rows={4}
              className="w-full bg-surface-3 border border-border rounded-lg px-4 py-3 text-sm text-ink placeholder-ink-dim focus:outline-none focus:border-amber resize-none transition-colors"
            />
          </div>
        ))}
      </div>

      <p className="text-xs font-mono text-ink-dim mt-4">
        Rellena el viernes o el domingo por la noche. Pulsa Guardar para persistir.
      </p>
    </div>
  );
}
