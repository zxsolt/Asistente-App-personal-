import { useEffect, useRef, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { fullTasksApi, actionsApi } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import type { FullTask, Action, ActionStatus } from '@/types';
import ConfettiBurst from './ConfettiBurst';

interface Props {
  task: FullTask;
  weekId: number;
  onDelete: () => void;
}

const STATUS_CYCLE: Record<ActionStatus, ActionStatus> = {
  pending: 'in_progress',
  in_progress: 'done',
  done: 'discarded',
  discarded: 'pending',
};

const STATUS_CONFIG: Record<ActionStatus, { label: string; cls: string }> = {
  pending:     { label: '⬜ Pendiente',   cls: 'bg-zinc-800/70 text-zinc-400' },
  in_progress: { label: '🔄 En curso',    cls: 'bg-blue-950/70 text-blue-400' },
  done:        { label: '✅ Hecho',       cls: 'bg-emerald-950/70 text-emerald-400' },
  discarded:   { label: '❌ Descartado', cls: 'bg-red-950/70 text-red-400' },
};

const DAYS = [
  { value: 'monday',             label: 'Lun' },
  { value: 'tuesday',            label: 'Mar' },
  { value: 'wednesday',          label: 'Mié' },
  { value: 'thursday',           label: 'Jue' },
  { value: 'friday',             label: 'Vie' },
  { value: 'saturday_morning',   label: 'Sáb m' },
  { value: 'saturday_afternoon', label: 'Sáb t' },
  { value: 'sunday_morning',     label: 'Dom m' },
  { value: 'sunday_afternoon',   label: 'Dom t' },
];

function clampMinutes(value: number): number {
  if (!Number.isFinite(value)) return 1;
  return Math.max(1, Math.min(10080, Math.floor(value)));
}

function InlineText({
  value,
  placeholder,
  multiline,
  onSave,
  className = '',
}: {
  value: string | null;
  placeholder: string;
  multiline?: boolean;
  onSave: (v: string) => void;
  className?: string;
}) {
  const [val, setVal] = useState(value ?? '');

  const save = () => {
    if (val !== (value ?? '')) onSave(val);
  };

  const base = `bg-transparent text-sm text-ink placeholder-ink-dim outline-none w-full resize-none focus:bg-surface-3 focus:px-2 focus:py-1 focus:rounded transition-all ${className}`;

  if (multiline) {
    return (
      <textarea
        value={val}
        placeholder={placeholder}
        onChange={(e) => setVal(e.target.value)}
        onBlur={save}
        rows={2}
        className={base}
      />
    );
  }
  return (
    <input
      type="text"
      value={val}
      placeholder={placeholder}
      onChange={(e) => setVal(e.target.value)}
      onBlur={save}
      className={base}
    />
  );
}

export default function TaskCard({ task, weekId, onDelete }: Props) {
  const [open, setOpen] = useState(false);
  const [budgetInput, setBudgetInput] = useState(task.time_budget_minutes?.toString() ?? '');
  const [limitMode, setLimitMode] = useState<'warn' | 'hard_stop'>(task.limit_mode);
  const [burst, setBurst] = useState<{ x: number; y: number } | null>(null);
  const [completing, setCompleting] = useState(false);
  const checkBtnRef = useRef<HTMLButtonElement>(null);
  const inv = () => queryClient.invalidateQueries({ queryKey: ['week', weekId] });

  const updateTask = useMutation({
    mutationFn: (d: Parameters<typeof fullTasksApi.update>[2]) =>
      fullTasksApi.update(weekId, task.id, d),
    onSuccess: inv,
  });

  const createAction = useMutation({
    mutationFn: () =>
      actionsApi.create(task.id, {
        order: (task.actions.length ?? 0) + 1,
        description: 'Nueva acción',
      }),
    onSuccess: inv,
  });

  const deleteAction = useMutation({
    mutationFn: (aid: number) => actionsApi.delete(task.id, aid),
    onSuccess: inv,
  });

  const updateAction = useMutation({
    mutationFn: (d: { id: number } & Parameters<typeof actionsApi.update>[2]) => {
      const { id, ...rest } = d;
      return actionsApi.update(task.id, id, rest);
    },
    onSuccess: inv,
  });

  const cycleStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: ActionStatus }) =>
      actionsApi.updateStatus(task.id, id, STATUS_CYCLE[status]),
    onSuccess: inv,
  });

  const totalActions = task.actions.length;
  const doneActions = task.actions.filter((a) => a.status === 'done').length;
  const progress = totalActions > 0 ? Math.round((doneActions / totalActions) * 100) : 0;
  const spentMinutes = Math.floor(task.time_spent_seconds / 60);
  const budgetMinutes = task.time_budget_minutes;
  const overBudget = budgetMinutes !== null && spentMinutes >= budgetMinutes;

  useEffect(() => {
    setBudgetInput(task.time_budget_minutes?.toString() ?? '');
  }, [task.time_budget_minutes]);

  useEffect(() => {
    setLimitMode(task.limit_mode);
  }, [task.limit_mode]);

  const saveBudget = () => {
    const trimmed = budgetInput.trim();
    if (!trimmed) {
      updateTask.mutate({ time_budget_minutes: null });
      return;
    }
    const parsed = Number(trimmed);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      setBudgetInput(task.time_budget_minutes?.toString() ?? '');
      return;
    }
    const next = clampMinutes(parsed);
    setBudgetInput(String(next));
    updateTask.mutate({ time_budget_minutes: next });
  };

  const handleComplete = (e: React.MouseEvent) => {
    e.stopPropagation();
    const btn = checkBtnRef.current;
    if (btn) {
      const rect = btn.getBoundingClientRect();
      setBurst({ x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 });
    }
    setCompleting(true);
    updateTask.mutate(
      { completed: true },
      { onError: () => setCompleting(false) },
    );
  };

  return (
    <>
      {burst && (
        <ConfettiBurst x={burst.x} y={burst.y} onDone={() => setBurst(null)} />
      )}
      <div
        className={`card overflow-hidden transition-all duration-500 ${
          completing ? 'opacity-0 scale-95 translate-y-2' : ''
        }`}
      >
        {/* Header */}
        <div
          className="px-5 py-4 flex items-center gap-3 cursor-pointer hover:bg-surface-2 transition-colors"
          onClick={() => setOpen((o) => !o)}
        >
          {/* Progress bar accent */}
          <div className="flex-shrink-0 w-1 h-8 rounded-full bg-surface-3 overflow-hidden">
            <div
              className="w-full bg-amber transition-all duration-500 rounded-full"
              style={{ height: `${progress}%` }}
            />
          </div>

          <div className="flex-1 min-w-0">
            <InlineText
              value={task.name}
              placeholder="Nombre de la tarea"
              onSave={(name) => updateTask.mutate({ name })}
              className="font-medium text-base"
            />
          </div>

          <div className="flex items-center gap-3 flex-shrink-0">
            <span
              className={`text-xs font-mono px-2 py-1 rounded-full ${
                overBudget ? 'text-status-discarded bg-red-950/40' : 'text-ink-dim bg-surface-3'
              }`}
            >
              {budgetMinutes !== null ? `${spentMinutes}/${budgetMinutes} min` : `${spentMinutes} min`}
            </span>
            {totalActions > 0 && (
              <span className="text-xs font-mono text-ink-dim">
                {doneActions}/{totalActions}
              </span>
            )}

            {/* Complete button */}
            <button
              ref={checkBtnRef}
              onClick={handleComplete}
              disabled={completing || updateTask.isPending}
              title="Marcar como completada"
              className="group relative w-7 h-7 flex items-center justify-center rounded-full border border-border hover:border-status-done hover:bg-emerald-950/40 transition-all active:animate-complete-pop disabled:opacity-50"
            >
              <svg
                viewBox="0 0 12 12"
                className="w-3.5 h-3.5 text-ink-dim group-hover:text-status-done transition-colors"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="2,6 5,9 10,3" />
              </svg>
            </button>

            {/* Delete button */}
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(); }}
              className="text-ink-dim hover:text-status-discarded transition-colors text-sm w-6 h-6 flex items-center justify-center rounded hover:bg-red-950/40"
              title="Eliminar tarea"
            >
              ×
            </button>
            <span className={`text-ink-dim text-xs font-mono transition-transform ${open ? 'rotate-90' : ''}`}>›</span>
          </div>
        </div>

        {/* Expanded content */}
        {open && (
          <div className="border-t border-border animate-slide-down">
            {/* Meta fields */}
            <div className="px-5 py-4 grid grid-cols-1 md:grid-cols-5 gap-4 bg-surface-2/40">
              {([
                { key: 'goal',         label: '🎯 Meta',          field: 'goal' as const },
                { key: 'milestone',    label: '📦 Hito',          field: 'milestone' as const },
                { key: 'milestone_dod',label: '✅ DoD del hito',  field: 'milestone_dod' as const },
              ] as const).map(({ key, label, field }) => (
                <div key={key}>
                  <p className="text-xs font-mono text-ink-dim mb-1">{label}</p>
                  <InlineText
                    value={task[field]}
                    placeholder={`${label}…`}
                    multiline
                    onSave={(v) => updateTask.mutate({ [field]: v || null } as any)}
                  />
                </div>
              ))}
              <div>
                <p className="text-xs font-mono text-ink-dim mb-1">⏱ Duración objetivo (min)</p>
                <input
                  type="number"
                  min={1}
                  value={budgetInput}
                  onChange={(e) => setBudgetInput(e.target.value)}
                  onBlur={saveBudget}
                  placeholder="Sin límite"
                  className="w-full bg-transparent text-sm text-ink placeholder-ink-dim outline-none focus:bg-surface-3 focus:px-2 focus:py-1 focus:rounded transition-all"
                />
              </div>
              <div>
                <p className="text-xs font-mono text-ink-dim mb-1">🚧 Límite</p>
                <select
                  value={limitMode}
                  onChange={(e) => {
                    const value = e.target.value as 'warn' | 'hard_stop';
                    setLimitMode(value);
                    updateTask.mutate({ limit_mode: value });
                  }}
                  className="w-full bg-transparent text-sm text-ink outline-none focus:bg-surface-3 focus:px-2 focus:py-1 focus:rounded transition-all"
                >
                  <option value="warn">Avisar</option>
                  <option value="hard_stop">Bloqueo duro</option>
                </select>
              </div>
            </div>

            {/* Actions table */}
            <div className="px-5 py-4">
              <div className="flex items-center justify-between mb-3">
                <p className="section-title mb-0">acciones</p>
                <button
                  onClick={() => createAction.mutate()}
                  disabled={createAction.isPending}
                  className="text-xs font-mono text-amber hover:text-amber-bright transition-colors disabled:opacity-50"
                >
                  + Añadir acción
                </button>
              </div>

              {task.actions.length === 0 ? (
                <p className="text-xs font-mono text-ink-dim py-2">Sin acciones todavía.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left border-b border-border">
                        <th className="pb-2 pr-3 text-xs font-mono text-ink-dim font-normal w-8">#</th>
                        <th className="pb-2 pr-3 text-xs font-mono text-ink-dim font-normal">Acción</th>
                        <th className="pb-2 pr-3 text-xs font-mono text-ink-dim font-normal hidden md:table-cell">DoD</th>
                        <th className="pb-2 pr-3 text-xs font-mono text-ink-dim font-normal w-24">Día</th>
                        <th className="pb-2 pr-3 text-xs font-mono text-ink-dim font-normal w-32">Estado</th>
                        <th className="pb-2 text-xs font-mono text-ink-dim font-normal w-8" />
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/50">
                      {task.actions.map((action) => (
                        <ActionRow
                          key={action.id}
                          action={action}
                          onDelete={() => deleteAction.mutate(action.id)}
                          onUpdate={(d) => updateAction.mutate({ id: action.id, ...d })}
                          onCycleStatus={() => cycleStatus.mutate({ id: action.id, status: action.status })}
                        />
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}

function ActionRow({
  action,
  onDelete,
  onUpdate,
  onCycleStatus,
}: {
  action: Action;
  onDelete: () => void;
  onUpdate: (d: Partial<{ description: string; dod: string | null; day: string | null; order: number }>) => void;
  onCycleStatus: () => void;
}) {
  const sc = STATUS_CONFIG[action.status];
  const isDiscarded = action.status === 'discarded';

  return (
    <tr className="group">
      {/* Order */}
      <td className="py-2 pr-3">
        <span className="text-xs font-mono text-ink-dim">{action.order}</span>
      </td>

      {/* Description */}
      <td className="py-2 pr-3">
        <input
          type="text"
          defaultValue={action.description}
          onBlur={(e) => {
            const v = e.target.value.trim();
            if (v && v !== action.description) onUpdate({ description: v });
          }}
          className={`inline-edit text-sm ${isDiscarded ? 'line-through text-ink-dim' : 'text-ink'}`}
        />
      </td>

      {/* DoD */}
      <td className="py-2 pr-3 hidden md:table-cell">
        <input
          type="text"
          defaultValue={action.dod ?? ''}
          placeholder="DoD…"
          onBlur={(e) => {
            const v = e.target.value.trim();
            if (v !== (action.dod ?? '')) onUpdate({ dod: v || null });
          }}
          className="inline-edit text-xs text-ink-muted"
        />
      </td>

      {/* Day */}
      <td className="py-2 pr-3">
        <select
          value={action.day ?? ''}
          onChange={(e) => onUpdate({ day: e.target.value || null })}
          className="bg-transparent text-xs font-mono text-ink-muted outline-none cursor-pointer hover:text-ink transition-colors"
        >
          <option value="">—</option>
          {DAYS.map((d) => (
            <option key={d.value} value={d.value}>{d.label}</option>
          ))}
        </select>
      </td>

      {/* Status */}
      <td className="py-2 pr-3">
        <button onClick={onCycleStatus} className={`status-badge ${sc.cls}`}>
          {sc.label}
        </button>
      </td>

      {/* Delete */}
      <td className="py-2">
        <button
          onClick={onDelete}
          className="opacity-0 group-hover:opacity-100 text-ink-dim hover:text-status-discarded transition-all text-xs w-5 h-5 flex items-center justify-center rounded hover:bg-red-950/40"
        >
          ×
        </button>
      </td>
    </tr>
  );
}
