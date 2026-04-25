import { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { weeksApi } from '@/lib/api';
import type { WeekDetail } from '@/types';
import TasksSection from '@/components/week/TasksSection';
import DistributionSection from '@/components/week/DistributionSection';
import ReviewSection from '@/components/week/ReviewSection';
import GlobalPomodoroSection from '@/components/week/GlobalPomodoroSection';

type Tab = 'work' | 'study' | 'dist' | 'timer' | 'review';

const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: 'work',   label: 'Trabajo',      icon: '💼' },
  { key: 'study',  label: 'Estudio',      icon: '📚' },
  { key: 'dist',   label: 'Distribución', icon: '📅' },
  { key: 'timer',  label: 'Timer Global', icon: '⏱️' },
  { key: 'review', label: 'Revisión',     icon: '🔁' },
];

function fmt(d: string) {
  return new Date(d + 'T00:00:00').toLocaleDateString('es-ES', {
    day: 'numeric', month: 'short', year: 'numeric',
  });
}

export default function WeekPage() {
  const { id } = useParams<{ id: string }>();
  const weekId = Number(id);
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>('work');

  const { data: week, isLoading, error } = useQuery<WeekDetail>({
    queryKey: ['week', weekId],
    queryFn: () => weeksApi.get(weekId),
    enabled: !!weekId,
  });

  return (
    <div className="min-h-screen bg-canvas flex flex-col">
      <div className="fixed inset-0 pointer-events-none opacity-[0.02]"
        style={{
          backgroundImage:
            'repeating-linear-gradient(0deg, #ddd8cf 0px, #ddd8cf 1px, transparent 1px, transparent 48px), repeating-linear-gradient(90deg, #ddd8cf 0px, #ddd8cf 1px, transparent 1px, transparent 48px)',
        }}
      />

      <header className="sticky top-0 z-20 bg-canvas/85 backdrop-blur-md border-b border-border">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center gap-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="text-ink-muted hover:text-ink font-mono text-sm transition-colors flex items-center gap-1"
            >
              ← Semanas
            </button>
            <Link to="/assistant" className="text-ink-muted hover:text-ink font-mono text-sm transition-colors">
              Asistente
            </Link>
            <Link to="/notes" className="text-ink-muted hover:text-ink font-mono text-sm transition-colors">
              Notas
            </Link>
          </div>
          <div className="w-px h-4 bg-border" />
          {week && (
            <span className="font-serif text-base text-ink">
              {fmt(week.start_date)} — {fmt(week.end_date)}
            </span>
          )}
        </div>
      </header>

      <div className="sticky top-14 z-10 bg-canvas/85 backdrop-blur-md border-b border-border">
        <div className="max-w-6xl mx-auto px-6 flex gap-0 overflow-x-auto">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`tab-btn whitespace-nowrap flex items-center gap-1.5 ${tab === t.key ? 'active' : ''}`}
            >
              <span className="text-sm">{t.icon}</span>
              <span>{t.label}</span>
            </button>
          ))}
        </div>
      </div>

      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8 animate-fade-in">
        {isLoading && (
          <div className="text-center py-20 text-ink-dim font-mono text-sm">Cargando semana…</div>
        )}
        {error && (
          <div className="text-center py-20 text-status-discarded font-mono text-sm">
            Error al cargar la semana.
          </div>
        )}
        {week && (
          <>
            <GlobalPomodoroSection week={week} visible={tab === 'timer'} />
            {tab === 'work'   && <TasksSection week={week} taskType="work" />}
            {tab === 'study'  && <TasksSection week={week} taskType="study" />}
            {tab === 'dist'   && <DistributionSection week={week} />}
            {tab === 'review' && <ReviewSection week={week} />}
          </>
        )}
      </main>
    </div>
  );
}
