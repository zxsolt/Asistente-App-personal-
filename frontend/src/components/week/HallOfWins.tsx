import { useMutation } from '@tanstack/react-query';
import { fullTasksApi } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import type { FullTask } from '@/types';

interface Props {
  tasks: FullTask[];
  weekId: number;
}

const TYPE_CONFIG = {
  work:  { color: 'text-work',  bg: 'bg-work/10',  border: 'border-work/20',  icon: '💼' },
  study: { color: 'text-study', bg: 'bg-study/10', border: 'border-study/20', icon: '📚' },
};

export default function HallOfWins({ tasks, weekId }: Props) {
  if (tasks.length === 0) return null;

  const inv = () => queryClient.invalidateQueries({ queryKey: ['week', weekId] });

  return (
    <div className="mt-10 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3 mb-5">
        <div className="flex-1 h-px bg-gradient-to-r from-amber/40 via-amber/10 to-transparent" />
        <div className="flex items-center gap-2 px-4 py-1.5 rounded-full border border-amber/30 bg-amber/5 animate-badge-pulse">
          <span className="text-lg">🏆</span>
          <span className="text-xs font-mono text-amber uppercase tracking-widest">Hall of Wins</span>
          <span className="text-xs font-mono text-amber/60 bg-amber/10 px-1.5 py-0.5 rounded-full">
            {tasks.length}
          </span>
        </div>
        <div className="flex-1 h-px bg-gradient-to-l from-amber/40 via-amber/10 to-transparent" />
      </div>

      {/* Completed tasks grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {tasks.map((task, i) => (
          <CompletedTaskCard
            key={task.id}
            task={task}
            weekId={weekId}
            index={i}
            onUndo={inv}
          />
        ))}
      </div>
    </div>
  );
}

function CompletedTaskCard({
  task,
  weekId,
  index,
  onUndo,
}: {
  task: FullTask;
  weekId: number;
  index: number;
  onUndo: () => void;
}) {
  const cfg = TYPE_CONFIG[task.task_type as 'work' | 'study'] ?? TYPE_CONFIG.work;
  const totalActions = task.actions.length;
  const doneActions = task.actions.filter((a) => a.status === 'done').length;
  const progress = totalActions > 0 ? Math.round((doneActions / totalActions) * 100) : 100;
  const spentMinutes = Math.floor(task.time_spent_seconds / 60);

  const undoMut = useMutation({
    mutationFn: () => fullTasksApi.update(weekId, task.id, { completed: false }),
    onSuccess: onUndo,
  });

  return (
    <div
      className={`group relative rounded-lg border ${cfg.border} ${cfg.bg} p-4 overflow-hidden animate-win-card-in`}
      style={{ animationDelay: `${index * 60}ms`, animationFillMode: 'both' }}
    >
      {/* Shimmer overlay */}
      <div
        className="absolute inset-0 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        style={{
          background: 'linear-gradient(105deg, transparent 40%, rgba(212,164,58,0.06) 50%, transparent 60%)',
          backgroundSize: '200% 100%',
        }}
      />

      {/* Top row */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-base flex-shrink-0">{cfg.icon}</span>
          <span className="text-sm font-medium text-ink line-through decoration-ink-dim/50 truncate">
            {task.name}
          </span>
        </div>
        <span className="text-lg flex-shrink-0 select-none">✅</span>
      </div>

      {/* Progress bar */}
      {totalActions > 0 && (
        <div className="mb-3">
          <div className="flex justify-between text-xs font-mono text-ink-dim mb-1">
            <span>{doneActions}/{totalActions} acciones</span>
            <span>{progress}%</span>
          </div>
          <div className="h-1 rounded-full bg-surface-3 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-amber to-status-done transition-all duration-700"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-ink-dim">
          {spentMinutes > 0 ? `${spentMinutes} min invertidos` : 'Sin tiempo registrado'}
        </span>
        <button
          onClick={() => undoMut.mutate()}
          disabled={undoMut.isPending}
          className="text-xs font-mono text-ink-dim hover:text-amber transition-colors opacity-0 group-hover:opacity-100 disabled:opacity-30"
          title="Deshacer completado"
        >
          ↩ deshacer
        </button>
      </div>
    </div>
  );
}
