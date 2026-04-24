import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { fullTasksApi, pomodoroPresetsApi } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import type { FullTask, PomodoroPreset, WeekDetail } from '@/types';
import { extractYoutubeVideoId, toYoutubeEmbedUrl } from '@/utils/youtube';

interface Props {
  week: WeekDetail;
  visible: boolean;
}

type Phase = 'idle' | 'focus' | 'short_break' | 'long_break';

interface PomodoroConfig {
  focus_minutes: number;
  short_break_minutes: number;
  long_break_minutes: number;
  cycles_before_long_break: number;
  music_url: string;
}

const DEFAULT_CONFIG: PomodoroConfig = {
  focus_minutes: 25,
  short_break_minutes: 5,
  long_break_minutes: 15,
  cycles_before_long_break: 4,
  music_url: '',
};

const PHASE_LABEL: Record<Phase, string> = {
  idle: 'Listo',
  focus: 'Foco',
  short_break: 'Descanso corto',
  long_break: 'Descanso largo',
};

function formatClock(totalSeconds: number): string {
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

function clampInt(value: number, min: number, max: number): number {
  if (!Number.isFinite(value)) return min;
  return Math.max(min, Math.min(max, Math.floor(value)));
}

function parseNumberInput(value: string, fallback: number): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return parsed;
}

interface PersistedTimerState {
  version: 1;
  saved_at_ms: number;
  config: PomodoroConfig;
  phase: Phase;
  isRunning: boolean;
  secondsLeft: number;
  focusCount: number;
  focusElapsed: number;
  pendingLoggedSeconds: number;
  selectedPresetId: number | '';
  selectedTaskId: number | '';
}

function storageKey(weekId: number): string {
  return `weekly_planner_global_pomodoro_v1_week_${weekId}`;
}

function normalizePhase(phase: unknown): Phase {
  if (phase === 'focus' || phase === 'short_break' || phase === 'long_break') return phase;
  return 'idle';
}

function catchUpTimerState(
  persisted: PersistedTimerState,
  selectedTask: FullTask | null,
): {
  phase: Phase;
  isRunning: boolean;
  secondsLeft: number;
  focusCount: number;
  focusElapsed: number;
  pendingLoggedSeconds: number;
} {
  let phase = normalizePhase(persisted.phase);
  let isRunning = !!persisted.isRunning;
  let secondsLeft = Math.max(0, Math.floor(persisted.secondsLeft || 0));
  let focusCount = Math.max(0, Math.floor(persisted.focusCount || 0));
  let focusElapsed = Math.max(0, Math.floor(persisted.focusElapsed || 0));
  let pendingLoggedSeconds = Math.max(0, Math.floor(persisted.pendingLoggedSeconds || 0));
  const elapsedSinceSave = Math.max(0, Math.floor((Date.now() - persisted.saved_at_ms) / 1000));

  if (!isRunning || elapsedSinceSave === 0) {
    return { phase, isRunning, secondsLeft, focusCount, focusElapsed, pendingLoggedSeconds };
  }

  let remaining = elapsedSinceSave;
  while (remaining > 0 && isRunning) {
    if (phase === 'idle') {
      phase = 'focus';
      secondsLeft = persisted.config.focus_minutes * 60;
    }

    const budgetSeconds = selectedTask?.time_budget_minutes ? selectedTask.time_budget_minutes * 60 : null;
    const hardStop = selectedTask?.limit_mode === 'hard_stop';
    const spentCommitted = selectedTask?.time_spent_seconds ?? 0;
    const spentUncommitted = pendingLoggedSeconds + focusElapsed;
    const alreadySpent = spentCommitted + spentUncommitted;

    if (phase === 'focus' && hardStop && budgetSeconds !== null && alreadySpent >= budgetSeconds) {
      isRunning = false;
      phase = 'idle';
      secondsLeft = persisted.config.focus_minutes * 60;
      focusElapsed = 0;
      break;
    }

    let step = Math.min(remaining, Math.max(secondsLeft, 1));
    if (phase === 'focus' && hardStop && budgetSeconds !== null) {
      const budgetLeft = Math.max(0, budgetSeconds - alreadySpent);
      step = Math.min(step, Math.max(budgetLeft, 0));
    }

    if (step <= 0) {
      isRunning = false;
      phase = 'idle';
      secondsLeft = persisted.config.focus_minutes * 60;
      focusElapsed = 0;
      break;
    }

    secondsLeft -= step;
    remaining -= step;
    if (phase === 'focus') {
      focusElapsed += step;
    }

    if (secondsLeft > 0) continue;

    if (phase === 'focus') {
      pendingLoggedSeconds += focusElapsed;
      focusElapsed = 0;
      focusCount += 1;
      const useLongBreak = focusCount % persisted.config.cycles_before_long_break === 0;
      phase = useLongBreak ? 'long_break' : 'short_break';
      secondsLeft = (useLongBreak ? persisted.config.long_break_minutes : persisted.config.short_break_minutes) * 60;
    } else {
      phase = 'focus';
      secondsLeft = persisted.config.focus_minutes * 60;
    }
  }

  return { phase, isRunning, secondsLeft, focusCount, focusElapsed, pendingLoggedSeconds };
}

export default function GlobalPomodoroSection({ week, visible }: Props) {
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const hydratedRef = useRef(false);
  const [config, setConfig] = useState<PomodoroConfig>(DEFAULT_CONFIG);
  const [phase, setPhase] = useState<Phase>('idle');
  const [isRunning, setIsRunning] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(DEFAULT_CONFIG.focus_minutes * 60);
  const [focusCount, setFocusCount] = useState(0);
  const [focusElapsed, setFocusElapsed] = useState(0);
  const [pendingLoggedSeconds, setPendingLoggedSeconds] = useState(0);
  const [presetName, setPresetName] = useState('');
  const [selectedPresetId, setSelectedPresetId] = useState<number | ''>('');
  const [selectedTaskId, setSelectedTaskId] = useState<number | ''>('');
  const [notice, setNotice] = useState<string | null>(null);

  const invalidateWeek = () => queryClient.invalidateQueries({ queryKey: ['week', week.id] });
  const invalidatePresets = () => queryClient.invalidateQueries({ queryKey: ['pomodoro-presets'] });

  const { data: presets = [] } = useQuery<PomodoroPreset[]>({
    queryKey: ['pomodoro-presets'],
    queryFn: pomodoroPresetsApi.list,
  });

  const logFocusMutation = useMutation({
    mutationFn: ({ taskId, seconds }: { taskId: number; seconds: number }) =>
      fullTasksApi.logFocus(week.id, taskId, { seconds }),
    onSuccess: invalidateWeek,
  });

  const createPresetMutation = useMutation({
    mutationFn: (d: Parameters<typeof pomodoroPresetsApi.create>[0]) => pomodoroPresetsApi.create(d),
    onSuccess: () => {
      invalidatePresets();
      setPresetName('');
      setNotice('Preset guardado.');
    },
  });

  const deletePresetMutation = useMutation({
    mutationFn: (id: number) => pomodoroPresetsApi.delete(id),
    onSuccess: () => {
      invalidatePresets();
      setSelectedPresetId('');
      setNotice('Preset eliminado.');
    },
  });

  const videoId = useMemo(() => extractYoutubeVideoId(config.music_url), [config.music_url]);

  useEffect(() => {
    hydratedRef.current = false;
  }, [week.id]);

  useEffect(() => {
    if (hydratedRef.current) return;
    hydratedRef.current = true;

    try {
      const raw = localStorage.getItem(storageKey(week.id));
      if (!raw) return;
      const parsed = JSON.parse(raw) as Partial<PersistedTimerState>;
      if (parsed.version !== 1) return;

      const restoredConfig: PomodoroConfig = {
        focus_minutes: clampInt(Number(parsed.config?.focus_minutes ?? DEFAULT_CONFIG.focus_minutes), 1, 180),
        short_break_minutes: clampInt(Number(parsed.config?.short_break_minutes ?? DEFAULT_CONFIG.short_break_minutes), 1, 60),
        long_break_minutes: clampInt(Number(parsed.config?.long_break_minutes ?? DEFAULT_CONFIG.long_break_minutes), 1, 120),
        cycles_before_long_break: clampInt(
          Number(parsed.config?.cycles_before_long_break ?? DEFAULT_CONFIG.cycles_before_long_break),
          1,
          12,
        ),
        music_url: typeof parsed.config?.music_url === 'string' ? parsed.config.music_url : '',
      };

      const fallbackTaskId = week.full_tasks[0]?.id ?? '';
      const restoredTaskId =
        typeof parsed.selectedTaskId === 'number' && week.full_tasks.some((t) => t.id === parsed.selectedTaskId)
          ? parsed.selectedTaskId
          : fallbackTaskId;
      const selectedTaskForCatchUp =
        week.full_tasks.find((t) => t.id === restoredTaskId) ?? null;

      const normalized: PersistedTimerState = {
        version: 1,
        saved_at_ms: Number(parsed.saved_at_ms ?? Date.now()),
        config: restoredConfig,
        phase: normalizePhase(parsed.phase),
        isRunning: !!parsed.isRunning,
        secondsLeft: clampInt(Number(parsed.secondsLeft ?? restoredConfig.focus_minutes * 60), 0, 10_000_000),
        focusCount: clampInt(Number(parsed.focusCount ?? 0), 0, 1_000_000),
        focusElapsed: clampInt(Number(parsed.focusElapsed ?? 0), 0, 1_000_000),
        pendingLoggedSeconds: clampInt(Number(parsed.pendingLoggedSeconds ?? 0), 0, 1_000_000),
        selectedPresetId: typeof parsed.selectedPresetId === 'number' ? parsed.selectedPresetId : '',
        selectedTaskId: restoredTaskId,
      };

      const resumed = catchUpTimerState(normalized, selectedTaskForCatchUp);
      setConfig(restoredConfig);
      setPhase(resumed.phase);
      setIsRunning(resumed.isRunning);
      setSecondsLeft(resumed.secondsLeft);
      setFocusCount(resumed.focusCount);
      setFocusElapsed(resumed.focusElapsed);
      setPendingLoggedSeconds(resumed.pendingLoggedSeconds);
      setSelectedPresetId(normalized.selectedPresetId);
      setSelectedTaskId(restoredTaskId);
      if (normalized.isRunning && !resumed.isRunning && selectedTaskForCatchUp?.limit_mode === 'hard_stop') {
        setNotice('Límite alcanzado mientras el timer estaba en segundo plano.');
      }
    } catch {
      // ignore broken state and start fresh
    }
  }, [week.id, week.full_tasks]);

  useEffect(() => {
    if (!hydratedRef.current) return;
    const payload: PersistedTimerState = {
      version: 1,
      saved_at_ms: Date.now(),
      config,
      phase,
      isRunning,
      secondsLeft,
      focusCount,
      focusElapsed,
      pendingLoggedSeconds,
      selectedPresetId,
      selectedTaskId,
    };
    localStorage.setItem(storageKey(week.id), JSON.stringify(payload));
  }, [
    config,
    phase,
    isRunning,
    secondsLeft,
    focusCount,
    focusElapsed,
    pendingLoggedSeconds,
    selectedPresetId,
    selectedTaskId,
    week.id,
  ]);

  useEffect(() => {
    if (!week.full_tasks.length) {
      setSelectedTaskId('');
      return;
    }
    const exists = week.full_tasks.some((t) => t.id === selectedTaskId);
    if (!exists) setSelectedTaskId(week.full_tasks[0].id);
  }, [week.full_tasks, selectedTaskId]);

  const selectedTask = useMemo(
    () => week.full_tasks.find((t) => t.id === selectedTaskId) ?? null,
    [week.full_tasks, selectedTaskId],
  );

  const budgetSeconds = selectedTask?.time_budget_minutes ? selectedTask.time_budget_minutes * 60 : null;
  const totalSpentSeconds = (selectedTask?.time_spent_seconds ?? 0) + pendingLoggedSeconds + focusElapsed;
  const hardLimitReached =
    !!selectedTask &&
    budgetSeconds !== null &&
    selectedTask.limit_mode === 'hard_stop' &&
    totalSpentSeconds >= budgetSeconds;

  useEffect(() => {
    if (phase === 'idle') setSecondsLeft(config.focus_minutes * 60);
  }, [phase, config.focus_minutes]);

  useEffect(() => {
    if (!presets.length || selectedPresetId !== '') return;
    setSelectedPresetId(presets[0].id);
  }, [presets, selectedPresetId]);

  useEffect(() => {
    if (selectedPresetId === '') return;
    const selected = presets.find((p) => p.id === selectedPresetId);
    if (!selected) return;
    setConfig({
      focus_minutes: selected.focus_minutes,
      short_break_minutes: selected.short_break_minutes,
      long_break_minutes: selected.long_break_minutes,
      cycles_before_long_break: selected.cycles_before_long_break,
      music_url: selected.music_url,
    });
  }, [selectedPresetId, presets]);

  useEffect(() => {
    if (!isRunning) return;
    const timer = window.setInterval(() => {
      setSecondsLeft((prev) => (prev > 0 ? prev - 1 : 0));
      if (phase === 'focus') setFocusElapsed((prev) => prev + 1);
    }, 1000);
    return () => window.clearInterval(timer);
  }, [isRunning, phase]);

  function sendPlayerCommand(func: 'playVideo' | 'pauseVideo') {
    const frame = iframeRef.current;
    if (!frame?.contentWindow) return;
    frame.contentWindow.postMessage(
      JSON.stringify({ event: 'command', func, args: [] }),
      '*',
    );
  }

  useEffect(() => {
    if (!videoId) return;
    if (isRunning && phase === 'focus') sendPlayerCommand('playVideo');
    else sendPlayerCommand('pauseVideo');
  }, [isRunning, phase, videoId]);

  useEffect(() => {
    return () => sendPlayerCommand('pauseVideo');
  }, []);

  const flushFocusElapsed = (taskIdParam?: number | '') => {
    const taskId = taskIdParam ?? selectedTaskId;
    if (taskId === '' || focusElapsed <= 0) {
      setFocusElapsed(0);
      return;
    }
    const seconds = focusElapsed;
    setPendingLoggedSeconds((prev) => prev + seconds);
    setFocusElapsed(0);
    logFocusMutation.mutate({ taskId, seconds });
  };

  useEffect(() => {
    if (!isRunning || phase !== 'focus' || !hardLimitReached || secondsLeft === 0) return;
    flushFocusElapsed();
    setIsRunning(false);
    setPhase('idle');
    setNotice('Límite de tiempo alcanzado para esta tarea.');
  }, [hardLimitReached, isRunning, phase, secondsLeft]);

  useEffect(() => {
    if (!isRunning || secondsLeft > 0) return;

    if (phase === 'focus') {
      flushFocusElapsed();
      const nextFocusCount = focusCount + 1;
      setFocusCount(nextFocusCount);
      const useLongBreak = nextFocusCount % config.cycles_before_long_break === 0;
      setPhase(useLongBreak ? 'long_break' : 'short_break');
      setSecondsLeft((useLongBreak ? config.long_break_minutes : config.short_break_minutes) * 60);
      return;
    }

    if (hardLimitReached) {
      setIsRunning(false);
      setPhase('idle');
      setNotice('Límite de tiempo alcanzado para esta tarea.');
      return;
    }
    setPhase('focus');
    setSecondsLeft(config.focus_minutes * 60);
  }, [
    config.cycles_before_long_break,
    config.focus_minutes,
    config.long_break_minutes,
    config.short_break_minutes,
    focusCount,
    hardLimitReached,
    isRunning,
    phase,
    secondsLeft,
  ]);

  useEffect(() => {
    if (!logFocusMutation.isSuccess) return;
    const id = window.setTimeout(() => setPendingLoggedSeconds(0), 400);
    return () => window.clearTimeout(id);
  }, [logFocusMutation.isSuccess, selectedTask?.time_spent_seconds]);

  useEffect(() => {
    if (phase === 'focus' && isRunning) return;
    if (selectedTaskId === '' || pendingLoggedSeconds <= 0 || logFocusMutation.isPending) return;
    logFocusMutation.mutate({ taskId: selectedTaskId, seconds: pendingLoggedSeconds });
  }, [phase, isRunning, pendingLoggedSeconds, selectedTaskId, logFocusMutation.isPending]);

  const canStart = !!selectedTask && !(selectedTask.limit_mode === 'hard_stop' && hardLimitReached);

  const handleStart = () => {
    if (!selectedTask) {
      setNotice('Selecciona una tarea para iniciar el Pomodoro global.');
      return;
    }
    if (selectedTask.limit_mode === 'hard_stop' && hardLimitReached) {
      setNotice('No puedes iniciar más focos: esta tarea ya alcanzó su límite.');
      return;
    }
    setNotice(null);
    if (phase === 'idle') {
      setPhase('focus');
      setSecondsLeft(config.focus_minutes * 60);
      setFocusElapsed(0);
    }
    setIsRunning(true);
  };

  const handlePause = () => {
    setIsRunning(false);
    setNotice(null);
  };

  const handleReset = () => {
    if (phase === 'focus' && focusElapsed > 0) flushFocusElapsed();
    setIsRunning(false);
    setPhase('idle');
    setSecondsLeft(config.focus_minutes * 60);
    setFocusElapsed(0);
    setNotice(null);
  };

  const saveAsPreset = () => {
    if (!presetName.trim()) {
      setNotice('Ponle nombre al preset.');
      return;
    }
    if (!videoId) {
      setNotice('El preset requiere un link válido de YouTube.');
      return;
    }
    createPresetMutation.mutate({
      name: presetName.trim(),
      ...config,
    });
  };

  const embedUrl = videoId ? toYoutubeEmbedUrl(videoId) : null;
  const spentMinutes = Math.floor(totalSpentSeconds / 60);
  const budgetMinutes = selectedTask?.time_budget_minutes ?? null;

  return (
    <div className={visible ? 'animate-fade-in' : 'hidden'} aria-hidden={!visible}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="section-title mb-1">temporizador global</p>
          <h2 className="font-serif text-2xl font-medium text-amber">Pomodoro + YouTube</h2>
        </div>
        <span className="text-xs font-mono text-ink-dim bg-surface-3 px-2.5 py-1 rounded-full">
          Ciclos foco: {focusCount}
        </span>
      </div>

      {week.full_tasks.length === 0 ? (
        <div className="card p-6 text-sm font-mono text-ink-dim">
          Crea al menos una tarea para usar el timer global.
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <div className="space-y-4">
            <div className="card p-3 bg-surface-2 border-border/70">
              <label className="block text-xs font-mono text-ink-dim mb-1">Tarea activa</label>
              <select
                value={selectedTaskId}
                onChange={(e) => {
                  const nextId = e.target.value ? Number(e.target.value) : '';
                  if (phase === 'focus' && focusElapsed > 0) flushFocusElapsed(selectedTaskId);
                  setIsRunning(false);
                  setPhase('idle');
                  setSecondsLeft(config.focus_minutes * 60);
                  setFocusElapsed(0);
                  setPendingLoggedSeconds(0);
                  setSelectedTaskId(nextId);
                }}
                className="w-full bg-surface-3 border border-border rounded px-3 py-2 text-sm text-ink focus:outline-none focus:border-amber transition-colors"
              >
                <option value="">—</option>
                {week.full_tasks.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.task_type === 'work' ? '💼' : '📚'} {t.name}
                  </option>
                ))}
              </select>
              {selectedTask && (
                <p className="text-xs font-mono text-ink-dim mt-2">
                  Tiempo: {spentMinutes} min
                  {budgetMinutes !== null ? ` / ${budgetMinutes} min` : ' (sin límite)'} ·{' '}
                  {selectedTask.limit_mode === 'hard_stop' ? 'bloqueo duro' : 'solo aviso'}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              <NumberField
                label="Foco"
                value={config.focus_minutes}
                min={1}
                max={180}
                disabled={isRunning}
                onChange={(v) => setConfig((prev) => ({ ...prev, focus_minutes: clampInt(v, 1, 180) }))}
              />
              <NumberField
                label="Descanso corto"
                value={config.short_break_minutes}
                min={1}
                max={60}
                disabled={isRunning}
                onChange={(v) => setConfig((prev) => ({ ...prev, short_break_minutes: clampInt(v, 1, 60) }))}
              />
              <NumberField
                label="Descanso largo"
                value={config.long_break_minutes}
                min={1}
                max={120}
                disabled={isRunning}
                onChange={(v) => setConfig((prev) => ({ ...prev, long_break_minutes: clampInt(v, 1, 120) }))}
              />
              <NumberField
                label="Ciclos"
                value={config.cycles_before_long_break}
                min={1}
                max={12}
                disabled={isRunning}
                onChange={(v) =>
                  setConfig((prev) => ({ ...prev, cycles_before_long_break: clampInt(v, 1, 12) }))
                }
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-ink-dim mb-1">URL YouTube</label>
              <input
                type="url"
                value={config.music_url}
                onChange={(e) => setConfig((prev) => ({ ...prev, music_url: e.target.value }))}
                placeholder="https://www.youtube.com/watch?v=..."
                className="w-full bg-surface-3 border border-border rounded px-3 py-2 text-sm text-ink focus:outline-none focus:border-amber transition-colors"
                disabled={isRunning}
              />
              {!videoId && config.music_url.trim() && (
                <p className="text-xs font-mono text-status-discarded mt-1">URL de YouTube no válida.</p>
              )}
              {!config.music_url.trim() && (
                <p className="text-xs font-mono text-ink-dim mt-1">Opcional: puedes usar el timer sin música.</p>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-2 items-end">
              <div>
                <label className="block text-xs font-mono text-ink-dim mb-1">Cargar preset</label>
                <select
                  value={selectedPresetId}
                  onChange={(e) => setSelectedPresetId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full bg-surface-3 border border-border rounded px-3 py-2 text-sm text-ink focus:outline-none focus:border-amber transition-colors"
                  disabled={isRunning}
                >
                  <option value="">—</option>
                  {presets.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={() => selectedPresetId && deletePresetMutation.mutate(selectedPresetId)}
                disabled={selectedPresetId === '' || deletePresetMutation.isPending || isRunning}
                className="btn-ghost disabled:opacity-50"
              >
                Borrar preset
              </button>
              <div>
                <label className="block text-xs font-mono text-ink-dim mb-1">Guardar como</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={presetName}
                    onChange={(e) => setPresetName(e.target.value)}
                    placeholder="Nombre"
                    className="w-full min-w-0 bg-surface-3 border border-border rounded px-3 py-2 text-sm text-ink focus:outline-none focus:border-amber transition-colors"
                    disabled={isRunning}
                  />
                  <button
                    onClick={saveAsPreset}
                    disabled={createPresetMutation.isPending || isRunning}
                    className="btn-primary disabled:opacity-50"
                  >
                    Guardar
                  </button>
                </div>
              </div>
            </div>

            <div className="card p-4 bg-surface-2 border-border/70">
              <div className="flex items-center justify-between gap-3 mb-2">
                <span className="text-xs font-mono text-ink-dim">{PHASE_LABEL[phase]}</span>
                <span className="text-xs font-mono text-ink-dim">
                  {selectedTask?.limit_mode === 'hard_stop' ? 'Bloqueo duro' : 'Solo aviso'}
                </span>
              </div>
              <div className="font-mono text-4xl text-amber mb-3">{formatClock(secondsLeft)}</div>
              <div className="flex gap-2 flex-wrap">
                {!isRunning ? (
                  <button onClick={handleStart} disabled={!canStart} className="btn-primary disabled:opacity-50">
                    Iniciar
                  </button>
                ) : (
                  <button onClick={handlePause} className="btn-ghost">Pausar</button>
                )}
                <button onClick={handleReset} className="btn-ghost">
                  Reiniciar
                </button>
              </div>
            </div>

            {notice && <p className="text-xs font-mono text-amber">{notice}</p>}
          </div>

          <div className="card p-2 bg-surface-2 border-border/70 min-h-[250px]">
            {embedUrl ? (
              <iframe
                ref={iframeRef}
                src={embedUrl}
                title="Pomodoro music"
                className="w-full aspect-video rounded"
                allow="autoplay; encrypted-media"
                allowFullScreen
              />
            ) : (
              <div className="w-full h-full min-h-[230px] flex items-center justify-center text-center text-xs font-mono text-ink-dim px-4">
                Pega una URL válida de YouTube para cargar la música.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function NumberField({
  label,
  value,
  min,
  max,
  disabled,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  disabled?: boolean;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <label className="block text-xs font-mono text-ink-dim mb-1">{label}</label>
      <input
        type="number"
        min={min}
        max={max}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(parseNumberInput(e.target.value, value))}
        className="w-full bg-surface-3 border border-border rounded px-2 py-2 text-sm text-ink focus:outline-none focus:border-amber transition-colors disabled:opacity-60"
      />
    </div>
  );
}
