import { useState, useEffect, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { distributionApi } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import type { WeekDetail, FullTask } from '@/types';

interface Props { week: WeekDetail }

const DAYS = [
  { key: 'monday',              label: 'Lunes',           defaultType: 'work' },
  { key: 'tuesday',             label: 'Martes',          defaultType: 'study' },
  { key: 'wednesday',           label: 'Miércoles',       defaultType: 'work' },
  { key: 'thursday',            label: 'Jueves',          defaultType: 'study' },
  { key: 'friday',              label: 'Viernes',         defaultType: 'work' },
  { key: 'saturday_morning',    label: 'Sábado mañana',   defaultType: 'study' },
  { key: 'saturday_afternoon',  label: 'Sábado tarde',    defaultType: 'work' },
  { key: 'sunday_morning',      label: 'Domingo mañana',  defaultType: 'rest' },
  { key: 'sunday_afternoon',    label: 'Domingo tarde',   defaultType: 'work' },
];

const TYPE_ICON: Record<string, string> = { work: '💼', study: '📚', rest: '😴' };
const TYPE_COLOR: Record<string, string> = { work: 'text-work', study: 'text-study', rest: 'text-ink-dim' };

interface RowState {
  day_type: string;
  task_ids: number[];   // IDs of assigned full_tasks
}

type DistMap = Record<string, RowState>;

function buildInitial(week: WeekDetail): DistMap {
  const map: DistMap = {};
  for (const d of DAYS) {
    const existing = week.daily_distributions.find((x) => x.day === d.key);
    // task_assignments stored as comma-separated IDs
    const ids = existing?.task_assignments
      ? existing.task_assignments.split(',').map(Number).filter(Boolean)
      : [];
    map[d.key] = {
      day_type: existing?.day_type ?? d.defaultType,
      task_ids: ids,
    };
  }
  return map;
}

export default function DistributionSection({ week }: Props) {
  const wid = week.id;
  const allTasks = week.full_tasks;
  const [rows, setRows] = useState<DistMap>(() => buildInitial(week));
  const [saved, setSaved] = useState(false);

  useEffect(() => { setRows(buildInitial(week)); }, [week.id]);

  const saveMut = useMutation({
    mutationFn: () =>
      distributionApi.upsert(
        wid,
        DAYS.map((d) => ({
          day: d.key,
          day_type: rows[d.key].day_type,
          // store IDs as strings
          task_assignments: rows[d.key].task_ids.map(String),
        })),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['week', wid] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  const setType = (key: string, val: string) =>
    setRows((r) => ({ ...r, [key]: { ...r[key], day_type: val } }));

  const toggleTask = (day: string, taskId: number) =>
    setRows((r) => {
      const ids = r[day].task_ids;
      return {
        ...r,
        [day]: {
          ...r[day],
          task_ids: ids.includes(taskId) ? ids.filter((i) => i !== taskId) : [...ids, taskId],
        },
      };
    });

  return (
    <div className="animate-fade-in">
      <div className="flex items-end justify-between mb-6">
        <div>
          <p className="section-title mb-1">📅 distribución</p>
          <h2 className="font-serif text-2xl font-medium text-ink">Distribución semanal</h2>
        </div>
        <div className="flex items-center gap-3">
          {saved && <span className="text-xs font-mono text-status-done animate-fade-in">✓ Guardado</span>}
          <button onClick={() => saveMut.mutate()} disabled={saveMut.isPending} className="btn-primary disabled:opacity-50">
            Guardar
          </button>
        </div>
      </div>

      {allTasks.length === 0 ? (
        <div className="card p-8 text-center">
          <p className="text-ink-dim font-mono text-sm">
            Añade tareas en las secciones 💼 Trabajo y 📚 Estudio primero.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {DAYS.map((d) => {
            const row = rows[d.key];
            const isRest = row.day_type === 'rest';
            const assignedTasks = allTasks.filter((t) => row.task_ids.includes(t.id));
            const availableTasks = allTasks.filter((t) => !row.task_ids.includes(t.id));

            return (
              <div key={d.key} className="card px-5 py-3 flex flex-col gap-2">
                <div className="flex items-center gap-3">
                  {/* Day name */}
                  <span className="font-mono text-sm text-ink w-36 flex-shrink-0">{d.label}</span>

                  {/* Day type selector */}
                  <select
                    value={row.day_type}
                    onChange={(e) => setType(d.key, e.target.value)}
                    className={`bg-transparent text-xs font-mono outline-none cursor-pointer w-28 flex-shrink-0 ${TYPE_COLOR[row.day_type] ?? 'text-ink-muted'}`}
                  >
                    <option value="work">💼 Trabajo</option>
                    <option value="study">📚 Estudio</option>
                    <option value="rest">😴 Descanso</option>
                  </select>

                  {/* Assigned task chips + add button */}
                  {!isRest && (
                    <div className="flex flex-wrap items-center gap-1.5 flex-1 min-w-0">
                      {assignedTasks.map((t) => (
                        <TaskChip
                          key={t.id}
                          task={t}
                          onRemove={() => toggleTask(d.key, t.id)}
                        />
                      ))}
                      {availableTasks.length > 0 && (
                        <TaskPicker
                          tasks={availableTasks}
                          onPick={(id) => toggleTask(d.key, id)}
                        />
                      )}
                    </div>
                  )}

                  {isRest && (
                    <span className="text-xs font-mono text-ink-dim">—</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <p className="text-xs font-mono text-ink-dim mt-3">
        Pulsa Guardar para persistir los cambios.
      </p>
    </div>
  );
}

function TaskChip({ task, onRemove }: { task: FullTask; onRemove: () => void }) {
  const isWork = task.task_type === 'work';
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-mono border ${
      isWork
        ? 'bg-blue-950/40 border-blue-900/40 text-work'
        : 'bg-purple-950/40 border-purple-900/40 text-study'
    }`}>
      <span>{isWork ? '💼' : '📚'}</span>
      <span className="max-w-[120px] truncate">{task.name}</span>
      <button
        onClick={onRemove}
        className="ml-0.5 opacity-50 hover:opacity-100 transition-opacity"
      >
        ×
      </button>
    </span>
  );
}

function TaskPicker({ tasks, onPick }: { tasks: FullTask[]; onPick: (id: number) => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-mono border border-dashed border-border-2 text-ink-dim hover:text-ink hover:border-amber/50 transition-colors"
      >
        + asignar
      </button>

      {open && (
        <div className="absolute left-0 top-7 z-30 bg-surface-2 border border-border-2 rounded-lg shadow-xl min-w-[200px] py-1 animate-slide-down">
          {tasks.map((t) => (
            <button
              key={t.id}
              onClick={() => { onPick(t.id); setOpen(false); }}
              className="w-full flex items-center gap-2 px-3 py-2 text-xs font-mono text-ink-muted hover:text-ink hover:bg-surface-3 transition-colors text-left"
            >
              <span>{t.task_type === 'work' ? '💼' : '📚'}</span>
              <span className="truncate">{t.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
