import { useState, KeyboardEvent } from 'react';
import { useMutation } from '@tanstack/react-query';
import { poolTasksApi } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import type { WeekDetail, PoolTask } from '@/types';

interface Props { week: WeekDetail }

type Col = 'work' | 'study';

const COL_CONFIG: Record<Col, { label: string; icon: string; color: string }> = {
  work:  { label: 'Trabajo',  icon: '💼', color: 'text-work' },
  study: { label: 'Estudio',  icon: '📚', color: 'text-study' },
};

export default function PoolSection({ week }: Props) {
  const wid = week.id;
  const inv = () => queryClient.invalidateQueries({ queryKey: ['week', wid] });

  const createMut = useMutation({
    mutationFn: (d: { title: string; task_type: string }) => poolTasksApi.create(wid, d),
    onSuccess: inv,
  });
  const deleteMut = useMutation({
    mutationFn: (tid: number) => poolTasksApi.delete(wid, tid),
    onSuccess: inv,
  });

  const [draft, setDraft] = useState<Record<Col, string>>({ work: '', study: '' });

  const submit = (col: Col) => {
    const title = draft[col].trim();
    if (!title) return;
    createMut.mutate({ title, task_type: col });
    setDraft((d) => ({ ...d, [col]: '' }));
  };

  const handleKey = (e: KeyboardEvent<HTMLInputElement>, col: Col) => {
    if (e.key === 'Enter') submit(col);
  };

  const byType = (t: Col) => week.pool_tasks.filter((p) => p.task_type === t);

  return (
    <div className="animate-fade-in">
      <div className="mb-6">
        <p className="section-title">pool de tareas</p>
        <p className="text-sm text-ink-muted font-mono">
          Vuelca aquí todo lo que quieres hacer esta semana antes de organizarlo.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {(['work', 'study'] as Col[]).map((col) => {
          const cfg = COL_CONFIG[col];
          const tasks = byType(col);
          return (
            <div key={col} className="card p-5">
              <div className="flex items-center gap-2 mb-4">
                <span>{cfg.icon}</span>
                <h3 className={`font-mono text-sm font-medium ${cfg.color}`}>{cfg.label}</h3>
                <span className="ml-auto text-xs font-mono text-ink-dim bg-surface-3 px-2 py-0.5 rounded-full">
                  {tasks.length}
                </span>
              </div>

              {/* Task list */}
              <ul className="space-y-1 mb-4 min-h-[40px]">
                {tasks.length === 0 && (
                  <li className="text-xs font-mono text-ink-dim py-2">Sin tareas aún</li>
                )}
                {tasks.map((t) => (
                  <PoolItem key={t.id} task={t} weekId={wid} onDelete={() => deleteMut.mutate(t.id)} />
                ))}
              </ul>

              {/* Add input */}
              <div className="flex items-center gap-2 border-t border-border pt-3">
                <input
                  type="text"
                  placeholder="+ Añadir tarea…"
                  value={draft[col]}
                  onChange={(e) => setDraft((d) => ({ ...d, [col]: e.target.value }))}
                  onKeyDown={(e) => handleKey(e, col)}
                  className="flex-1 bg-transparent text-sm text-ink placeholder-ink-dim outline-none"
                />
                <button
                  onClick={() => submit(col)}
                  disabled={!draft[col].trim()}
                  className="text-xs font-mono text-amber hover:text-amber-bright disabled:opacity-30 transition-colors"
                >
                  ↵
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PoolItem({ task, weekId, onDelete }: { task: PoolTask; weekId: number; onDelete: () => void }) {
  const [editing, setEditing] = useState(false);
  const [val, setVal] = useState(task.title);

  const updateMut = useMutation({
    mutationFn: (title: string) => poolTasksApi.update(weekId, task.id, { title }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['week', weekId] }),
  });

  const save = () => {
    const t = val.trim();
    if (t && t !== task.title) updateMut.mutate(t);
    else setVal(task.title);
    setEditing(false);
  };

  return (
    <li className="group flex items-center gap-2 px-2 py-1.5 rounded hover:bg-surface-3 transition-colors">
      <span className="w-1 h-1 rounded-full bg-ink-dim flex-shrink-0" />
      {editing ? (
        <input
          autoFocus
          value={val}
          onChange={(e) => setVal(e.target.value)}
          onBlur={save}
          onKeyDown={(e) => { if (e.key === 'Enter') save(); if (e.key === 'Escape') { setVal(task.title); setEditing(false); } }}
          className="flex-1 bg-transparent text-sm text-ink outline-none"
        />
      ) : (
        <span
          className="flex-1 text-sm text-ink cursor-text"
          onDoubleClick={() => setEditing(true)}
        >
          {task.title}
        </span>
      )}
      <button
        onClick={onDelete}
        className="opacity-0 group-hover:opacity-100 text-ink-dim hover:text-status-discarded transition-all text-xs w-5 h-5 flex items-center justify-center rounded hover:bg-red-950/40"
      >
        ×
      </button>
    </li>
  );
}
