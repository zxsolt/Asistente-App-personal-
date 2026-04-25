export type ActionStatus = 'pending' | 'in_progress' | 'done' | 'discarded';
export type TaskType = 'work' | 'study';
export type TaskPriority = 'low' | 'medium' | 'high';

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
  priority: TaskPriority | null;
  due_at: string | null;
  source: string | null;
  source_ref: string | null;
  natural_language_input: string | null;
  actions: Action[];
}

export interface Note {
  id: number;
  user_id: number;
  content: string;
  category: string;
  source: string;
  source_ref: string | null;
  created_at: string;
  updated_at: string;
}

export interface TelegramLink {
  id: number;
  user_id: number;
  telegram_chat_id: number | null;
  telegram_user_id: number | null;
  telegram_username: string | null;
  is_active: boolean;
  pending_link_expires_at: string | null;
  last_seen_at: string | null;
}

export interface TelegramLinkCode {
  code: string;
  expires_at: string;
}

export interface AssistantMessageRequest {
  message: string;
  channel: 'web' | 'telegram';
  metadata?: Record<string, unknown>;
}

export interface AssistantMessageResponse {
  reply_text: string;
  intent:
    | 'task_create'
    | 'task_query'
    | 'note_create'
    | 'note_query'
    | 'reminder_create'
    | 'reminder_query'
    | 'week_create'
    | 'general_query'
    | 'unknown';
  decision: 'act' | 'answer' | 'clarify';
  action_taken: string;
  entities: Record<string, unknown>;
  used_ai: boolean;
  persistence_mode: 'draft' | 'applied' | 'none';
  confidence: number;
  rationale_summary: string | null;
  planning_json: {
    tasks_detected: Array<{
      title: string;
      task_type: 'work' | 'study' | 'fitness' | 'personal';
      phase: string | null;
      source_clause: string | null;
      inferred: boolean;
    }>;
    schedule: Array<{
      day: string;
      blocked: boolean;
      tasks: Array<{
        title: string;
        task_type: 'work' | 'study' | 'fitness' | 'personal';
        phase: string | null;
        source_clause: string | null;
        inferred: boolean;
      }>;
    }>;
    reasoning: string;
  } | null;
}

export interface AssistantNotification {
  id: number;
  kind: string;
  title: string;
  message: string;
  payload: Record<string, unknown>;
  channel_targets: string[];
  status: string;
  source: string;
  created_at: string;
  sent_at: string | null;
  read_at: string | null;
  last_error: string | null;
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
