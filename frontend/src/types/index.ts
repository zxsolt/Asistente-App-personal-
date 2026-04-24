export type ActionStatus = 'pending' | 'in_progress' | 'done' | 'discarded';
export type TaskType = 'work' | 'study';

export interface User {
  id: number;
  username: string;
  email: string;
}

export interface Week {
  id: number;
  start_date: string;
  end_date: string;
}

export interface PoolTask {
  id: number;
  week_id: number;
  title: string;
  task_type: TaskType;
}

export interface Action {
  id: number;
  full_task_id: number;
  order: number;
  description: string;
  dod: string | null;
  day: string | null;
  status: ActionStatus;
}

export interface FullTask {
  id: number;
  week_id: number;
  name: string;
  task_type: TaskType;
  goal: string | null;
  milestone: string | null;
  milestone_dod: string | null;
  time_budget_minutes: number | null;
  time_spent_seconds: number;
  limit_mode: 'warn' | 'hard_stop';
  completed: boolean;
  actions: Action[];
}

export interface PomodoroPreset {
  id: number;
  user_id: number;
  name: string;
  focus_minutes: number;
  short_break_minutes: number;
  long_break_minutes: number;
  cycles_before_long_break: number;
  music_url: string;
}

export interface DailyDistribution {
  id: number;
  week_id: number;
  day: string;
  day_type: string | null;
  task_assignments: string | null;
}

export interface WeeklyReview {
  id: number;
  week_id: number;
  closed_this_week: string | null;
  pending_why: string | null;
  moving_to_next_week: string | null;
}

export interface WeekDetail extends Week {
  pool_tasks: PoolTask[];
  full_tasks: FullTask[];
  daily_distributions: DailyDistribution[];
  weekly_review: WeeklyReview | null;
}
