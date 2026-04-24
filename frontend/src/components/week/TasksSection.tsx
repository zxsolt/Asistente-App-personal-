import { useState, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { fullTasksApi } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import type { WeekDetail, TaskType } from '@/types';
import TaskCard from './TaskCard';
import HallOfWins from './HallOfWins';

interface Props { week: WeekDetail; taskType: TaskType }

const CONFIG: Record<TaskType, { icon: string; label: string; color: string; placeholder: string }> = {
  work:  { icon: '💼', label: 'Tareas de Trabajo',  color: 'text-work',  placeholder: 'Ej: Preparar informe trimestral…' },
  study: { icon: '📚', label: 'Tareas de Estudio', color: 'text-study', placeholder: 'Ej: Leer capítulo 3 de Clean Code…' },
};

export default function TasksSection({ week, taskType }: Props) {
  const cfg = CONFIG[taskType];
  const wid = week.id;
  const allTasks = week.full_tasks.filter((t) => t.task_type === taskType);
  const activeTasks = allTasks.filter((t) => !t.completed);
  const completedTasks = allTasks.filter((t) => t.completed);
  const inv = () => queryClient.invalidateQueries({ queryKey: ['week', wid] });

  const [name, setName] = useState('');
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const createMut = useMutation({
    mutationFn: () => fullTasksApi.create(wid, { name: name.trim(), task_type: taskType }),
    onSuccess: () => { inv(); setName(''); inputRef.current?.focus(); },
  });

  const deleteMut = useMutation({
    mutationFn: (tid: number) => fullTasksApi.delete(wid, tid),
    onSuccess: inv,
  });

  const submit = () => { if (name.trim()) createMut.mutate(); };

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="section-title mb-1">{cfg.icon} sección</p>
          <h2 className={`font-serif text-2xl font-medium ${cfg.color}`}>{cfg.label}</h2>
        </div>
        <span className="text-xs font-mono text-ink-dim bg-surface-3 px-2.5 py-1 rounded-full">
          {activeTasks.length} {activeTasks.length === 1 ? 'tarea activa' : 'tareas activas'}
        </span>
      </div>

      {/* Active task cards */}
      <div className="space-y-3 mb-4">
        {activeTasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            weekId={wid}
            onDelete={() => deleteMut.mutate(task.id)}
          />
        ))}
      </div>

      {/* Inline add — always visible at the bottom */}
      <div
        className={`card px-5 py-4 flex items-center gap-3 transition-all ${
          focused ? 'border-amber/50 bg-surface-2' : 'border-dashed hover:border-border-2'
        }`}
      >
        <span className={`text-lg transition-opacity ${focused ? 'opacity-100' : 'opacity-30'}`}>
          {cfg.icon}
        </span>
        <input
          ref={inputRef}
          type="text"
          placeholder={focused ? cfg.placeholder : `+ Añadir tarea de ${taskType === 'work' ? 'trabajo' : 'estudio'}…`}
          value={name}
          onChange={(e) => setName(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') submit();
            if (e.key === 'Escape') { setName(''); inputRef.current?.blur(); }
          }}
          className="flex-1 bg-transparent text-sm text-ink placeholder-ink-dim outline-none"
        />
        {name.trim() && (
          <button
            onMouseDown={(e) => { e.preventDefault(); submit(); }}
            disabled={createMut.isPending}
            className="btn-primary text-xs py-1.5 disabled:opacity-50 flex-shrink-0"
          >
            {createMut.isPending ? '…' : 'Añadir'}
          </button>
        )}
      </div>

      {activeTasks.length === 0 && completedTasks.length === 0 && !focused && (
        <p className="text-center text-xs font-mono text-ink-dim mt-4">
          Sin tareas todavía — escribe arriba para añadir la primera.
        </p>
      )}

      {activeTasks.length === 0 && completedTasks.length > 0 && !focused && (
        <p className="text-center text-xs font-mono text-ink-dim mt-4">
          🎉 ¡Todas las tareas completadas esta semana!
        </p>
      )}

      {/* Hall of Wins */}
      <HallOfWins tasks={completedTasks} weekId={wid} />
    </div>
  );
}
