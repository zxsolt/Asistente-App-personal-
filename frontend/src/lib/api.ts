import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL ?? '/api';

export const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('planner_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('planner_token');
      window.location.href = '/auth';
    }
    return Promise.reject(err);
  },
);

// ─── Auth ────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (d: { username: string; password: string }) =>
    api.post('/auth/login', d).then((r) => r.data),
  register: (d: { username: string; email: string; password: string }) =>
    api.post('/auth/register', d).then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
};

// ─── Weeks ───────────────────────────────────────────────────────────────────

export const weeksApi = {
  list: () => api.get('/weeks/').then((r) => r.data),
  get: (id: number) => api.get(`/weeks/${id}`).then((r) => r.data),
  create: (d: { start_date: string; end_date: string }) =>
    api.post('/weeks/', d).then((r) => r.data),
  update: (id: number, d: Partial<{ start_date: string; end_date: string }>) =>
    api.patch(`/weeks/${id}`, d).then((r) => r.data),
  delete: (id: number) => api.delete(`/weeks/${id}`),
};

// ─── Pool Tasks ───────────────────────────────────────────────────────────────

export const poolTasksApi = {
  create: (weekId: number, d: { title: string; task_type: string }) =>
    api.post(`/weeks/${weekId}/pool-tasks/`, d).then((r) => r.data),
  update: (weekId: number, tid: number, d: { title?: string; task_type?: string }) =>
    api.patch(`/weeks/${weekId}/pool-tasks/${tid}`, d).then((r) => r.data),
  delete: (weekId: number, tid: number) =>
    api.delete(`/weeks/${weekId}/pool-tasks/${tid}`),
};

// ─── Full Tasks ───────────────────────────────────────────────────────────────

export const fullTasksApi = {
  create: (
    weekId: number,
    d: {
      name: string;
      task_type: string;
      goal?: string;
      milestone?: string;
      milestone_dod?: string;
      time_budget_minutes?: number | null;
      limit_mode?: 'warn' | 'hard_stop';
      priority?: 'low' | 'medium' | 'high' | null;
      due_at?: string | null;
      source?: string | null;
      source_ref?: string | null;
      natural_language_input?: string | null;
    },
  ) => api.post(`/weeks/${weekId}/tasks/`, d).then((r) => r.data),
  update: (
    weekId: number,
    tid: number,
    d: Partial<{
      name: string;
      goal: string | null;
      milestone: string | null;
      milestone_dod: string | null;
      time_budget_minutes: number | null;
      limit_mode: 'warn' | 'hard_stop';
      completed: boolean;
      priority: 'low' | 'medium' | 'high' | null;
      due_at: string | null;
      source: string | null;
      source_ref: string | null;
      natural_language_input: string | null;
    }>,
  ) => api.patch(`/weeks/${weekId}/tasks/${tid}`, d).then((r) => r.data),
  logFocus: (weekId: number, tid: number, d: { seconds: number }) =>
    api.post(`/weeks/${weekId}/tasks/${tid}/log-focus`, d).then((r) => r.data),
  delete: (weekId: number, tid: number) =>
    api.delete(`/weeks/${weekId}/tasks/${tid}`),
};

// ─── Actions ──────────────────────────────────────────────────────────────────

export const actionsApi = {
  create: (
    taskId: number,
    d: { order: number; description: string; dod?: string; day?: string; status?: string },
  ) => api.post(`/tasks/${taskId}/actions/`, d).then((r) => r.data),
  update: (
    taskId: number,
    aid: number,
    d: Partial<{ order: number; description: string; dod: string | null; day: string | null; status: string }>,
  ) => api.patch(`/tasks/${taskId}/actions/${aid}`, d).then((r) => r.data),
  updateStatus: (taskId: number, aid: number, status: string) =>
    api.patch(`/tasks/${taskId}/actions/${aid}/status`, { status }).then((r) => r.data),
  delete: (taskId: number, aid: number) =>
    api.delete(`/tasks/${taskId}/actions/${aid}`),
};

// ─── Distribution ─────────────────────────────────────────────────────────────

export const distributionApi = {
  upsert: (weekId: number, d: Array<{ day: string; day_type?: string; task_assignments: string[] }>) =>
    api.put(`/weeks/${weekId}/distribution/`, d).then((r) => r.data),
};

// ─── Review ───────────────────────────────────────────────────────────────────

export const reviewApi = {
  upsert: (
    weekId: number,
    d: { closed_this_week?: string | null; pending_why?: string | null; moving_to_next_week?: string | null },
  ) => api.put(`/weeks/${weekId}/review/`, d).then((r) => r.data),
};

// ─── Pomodoro Presets ────────────────────────────────────────────────────────

export const pomodoroPresetsApi = {
  list: () => api.get('/pomodoro-presets/').then((r) => r.data),
  create: (d: {
    name: string;
    focus_minutes: number;
    short_break_minutes: number;
    long_break_minutes: number;
    cycles_before_long_break: number;
    music_url: string;
  }) => api.post('/pomodoro-presets/', d).then((r) => r.data),
  delete: (id: number) => api.delete(`/pomodoro-presets/${id}`),
};

// ─── Assistant ───────────────────────────────────────────────────────────────

export const assistantApi = {
  sendMessage: (d: {
    message: string;
    channel: 'web' | 'telegram';
    metadata?: Record<string, unknown>;
  }) => api.post('/assistant/message', d).then((r) => r.data),
  listNotifications: () => api.get('/assistant/notifications').then((r) => r.data),
  markNotificationRead: (notificationId: number) =>
    api.post(`/assistant/notifications/${notificationId}/read`).then((r) => r.data),
};

// ─── Notes ───────────────────────────────────────────────────────────────────

export const notesApi = {
  list: () => api.get('/notes/').then((r) => r.data),
  create: (d: {
    content: string;
    category?: string;
    source?: string;
    source_ref?: string | null;
  }) => api.post('/notes/', d).then((r) => r.data),
};

// ─── Telegram ────────────────────────────────────────────────────────────────

export const telegramApi = {
  getLink: () => api.get('/telegram/link').then((r) => r.data),
  createLinkCode: () => api.post('/telegram/link-code').then((r) => r.data),
};
