# Autonomous Assistant Design

## Goal

Evolve the current planner application into a real personal assistant with two coordinated behaviors:

1. A reactive assistant agent that can read the full user database and perform controlled write actions when the user interacts with it.
2. A proactive watcher that only reads the database, detects relevant situations, and sends notifications through web and Telegram without modifying user data.

This design explicitly avoids turning the system into a command-only router. The assistant should reason over the user's full context and choose useful actions, while preserving safety boundaries around destructive changes.

## Product Behavior

### Reactive assistant

The reactive assistant is the main conversational agent used through web and Telegram. It should:

- read the full user context with prioritization
- reason over current workload, history, notes, reminders, and existing plans
- decide whether to answer, create, update, complete, or reorganize data
- accept natural instructions such as reminder creation, task planning, and follow-up questions

The assistant may write to the database only through explicit application tools. It must not perform arbitrary SQL-like freeform writes.

### Proactive watcher

The proactive watcher is a separate background component. It should:

- only read the database
- detect conditions worth surfacing to the user
- create notification records and dispatch them to web and Telegram
- never create, edit, delete, or rebalance planner data on its own

This separation ensures the proactive system remains helpful without becoming invasive or destructive.

## Scope

This design covers:

- backend architecture changes for an agent-based assistant
- a notification model for proactive alerts
- background watcher logic
- web and Telegram delivery integration
- audit boundaries between agent writes and watcher reads

This design does not yet include:

- voice/Whisper work
- fitness module expansion
- scheduled autonomous replanning
- long-form daily briefings or coaching behavior

## Current System Baseline

The repository already contains:

- planner data models for weeks, tasks, actions, and distributions
- assistant modules with classifier, planner, notes, reminders, Telegram integration, and OpenRouter access
- frontend assistant and notes pages
- a planner draft layer that can return planning proposals

The new design must extend these parts rather than replacing them.

## Architecture

### 1. Memory and context layer

Introduce a shared context service as the single read entry point for assistant reasoning and watcher evaluation.

Responsibilities:

- collect all relevant user data from the existing database
- prioritize active and recent information first
- expand to historical information when needed
- return normalized context packets for downstream consumers

Context packet structure:

- `active_context`
  current week, upcoming tasks, open reminders, unfinished work
- `recent_context`
  recent tasks, last notes, recent actions, recent completions
- `historical_context`
  older related items used for continuity and pattern detection
- `constraints`
  blocked days, overloaded periods, empty periods, stale items
- `relevant_entities`
  the subset of tasks, weeks, reminders, notes, and actions most relevant to the current reasoning step

This service will build on the existing planner context logic but become the formal dependency for both the assistant agent and proactive watcher.

### 2. Reactive assistant agent

Replace the current mental model of “intent -> hardcoded action” with an agent loop that still uses application tools and safety policies.

Responsibilities:

- interpret user requests in context
- decide whether the best result is a reply, a write action, a planning proposal, or a clarification
- use tool calls for all writes
- attach rationale metadata to each action

Allowed write capabilities:

- create task
- update task
- complete task
- create week
- rebalance week
- create note
- create reminder
- update reminder

Forbidden autonomous write capabilities:

- bulk destructive deletion
- arbitrary historical rewrite
- mass planner resets

The assistant is allowed to act automatically when interacting with the user if confidence is high and the action is consistent with current context.

### 3. Proactive watcher

Add a background watcher service that runs periodically and evaluates all users independently.

Responsibilities:

- load prioritized context for a user
- run a fixed set of proactive detectors
- create notification records when a detector fires
- deduplicate repeated alerts
- dispatch notifications through available channels

The watcher never writes planner state. It only writes notification state and delivery state.

Initial detectors:

- `reminder_due`
  a reminder is due or about to be due
- `today_empty`
  the user has no meaningful plan for today
- `today_overloaded`
  today appears overloaded compared with surrounding days
- `stale_task`
  an important task has been idle for too long
- `week_gap`
  the current week exists but lacks structure or is nearly empty
- `follow_up_hint`
  the system detects likely continuity or pending next-step work based on recent history

Detectors intentionally excluded from the first phase:

- fitness coaching
- motivational summaries
- autonomous rescheduling
- high-frequency nudges

### 4. Notification layer

Introduce an application-level notification model and service.

New entity: `assistant_notifications`

Suggested fields:

- `id`
- `user_id`
- `kind`
- `title`
- `message`
- `payload_json`
- `channel_targets`
- `status`
- `dedupe_key`
- `created_at`
- `sent_at`
- `read_at`

Behavior:

- every proactive watcher alert creates a notification record
- notifications can be delivered to web, Telegram, or both
- repeated detector hits should reuse a dedupe key window so the same alert is not sent continuously
- web should keep a visible notification history
- Telegram should receive only meaningful alerts and reminder-style events

### 5. Delivery integration

#### Web delivery

Add assistant notifications to the frontend so the user can see a feed of generated alerts. The web channel does not need push infrastructure in the first implementation; polling or page-load fetch is enough.

#### Telegram delivery

Reuse the existing Telegram integration. Add outbound message sending for proactive notifications and reminders. Telegram dispatch must be conditional on the user having a linked Telegram chat.

Priority guidance:

- `reminder_due`: web + Telegram
- `today_empty`: web, optional Telegram
- `today_overloaded`: web
- `stale_task`: web, optional Telegram if high confidence
- `week_gap`: web
- `follow_up_hint`: web, optional Telegram

## Data Model Changes

### Existing models to reuse

- `full_tasks`
- `weeks`
- `actions`
- `notes`
- `reminders`
- `telegram_links`

### New models

#### assistant_notifications

Tracks proactive notifications and their lifecycle.

#### optional assistant_runs

A lightweight audit table for agent decisions can be added if needed. This is optional in the first implementation if rationale metadata is already captured in logs and action payloads.

## Agent Policy

### Read policy

The assistant agent and proactive watcher both get logical read access to the full user database, mediated by the shared context service.

The prioritization strategy is:

1. active context
2. recent context
3. historical context on demand

### Write policy

Only the reactive assistant may write planner data, and only through system tools.

Each write action must capture:

- source: `assistant_agent`
- action kind
- target entity ids
- short rationale summary
- timestamp

### Proactive policy

The proactive watcher may:

- read user data
- infer useful alerts
- create notifications
- send notifications

The proactive watcher may not:

- create tasks
- update tasks
- mark tasks completed
- change weeks
- create notes on behalf of the user
- create reminders without user input

## Reminder Handling

The assistant should support natural reminder creation such as:

- `recuerdame en 10 minutos llamar a X`
- `mañana recuérdame comprar pan`

Flow:

1. reactive assistant parses and creates a reminder record
2. proactive watcher notices it when due
3. notification layer emits delivery to web and Telegram

This keeps reminder execution inside the read-only watcher while allowing reminder creation through the conversational agent.

## API Surface

### Assistant API

Extend the assistant response contract so the frontend can distinguish between:

- informational reply
- action performed
- planning proposal
- caution or clarification

The response should include:

- `reply_text`
- `action_taken`
- `intent`
- `used_ai`
- `persistence_mode`
- `planning_json`
- `confidence`
- `rationale_summary`

### Notification API

Add endpoints such as:

- `GET /assistant/notifications`
- `POST /assistant/notifications/{id}/read`

A background process will populate these records; the frontend only needs retrieval and read-state updates in the first phase.

## Frontend Integration

The existing assistant page should stay as the main conversation surface. Add:

- notification feed or panel
- rendering for assistant confidence and action summaries when useful
- reminder confirmation display
- future room for “apply” or “undo” patterns

The initial UI scope stays modest. The major requirement is that proactive notifications are visible and distinct from chat replies.

## Telegram Integration

Reuse the current Telegram link flow. Extend it with outbound proactive sends.

Requirements:

- if a user has a linked Telegram chat, the watcher may send supported notification kinds
- if Telegram delivery fails, keep the notification in failed or pending state without affecting planner data
- Telegram replies from the user continue to flow through the reactive assistant

## Error Handling

### Assistant agent

- if reasoning fails, return a normal fallback reply without partial destructive writes
- if a tool write fails, return a clear failure response and log the attempted action
- if context loading fails, degrade gracefully to smaller-scope reasoning

### Proactive watcher

- if a detector fails, continue other detectors for that user
- if a single user evaluation fails, continue with other users
- if Telegram delivery fails, preserve notification state for retry or inspection
- if notification dedupe fails, prefer under-sending to over-sending

## Observability

Add structured logs for:

- agent reasoning mode
- tools invoked
- context scope used
- watcher detector hits
- notification dispatch result
- dedupe skips

This is essential because an assistant that “thinks” but leaves no audit trail becomes impossible to trust.

## Rollout Plan

### Phase 1

- formalize shared context service
- introduce assistant notification table and service
- add proactive watcher skeleton with `reminder_due` and `today_empty`
- add web notification retrieval
- add Telegram notification delivery

### Phase 2

- move current assistant service toward agent-with-tools orchestration
- add rationale metadata and confidence handling
- add `today_overloaded`, `stale_task`, `week_gap`, `follow_up_hint`

### Phase 3

- improve frontend notification UX
- refine autonomy thresholds
- add optional undo affordances for assistant writes

## Testing Strategy

### Unit tests

- context prioritization
- detector triggering and deduplication
- reminder due logic
- agent write policy checks

### Integration tests

- reminder creation through assistant -> reminder fires -> notification stored
- today-empty detector -> notification record generated
- linked Telegram user receives outbound notification path
- assistant task write includes rationale metadata

### Regression focus

- existing planner routes remain functional
- current assistant endpoints keep compatibility
- Telegram linking still works
- frontend assistant and notes pages do not regress

## Recommendation

Implement this as an agent overlay on the existing planner system, not as a rewrite. The current codebase already has enough primitives to support a real assistant, but it needs a stronger policy split:

- reactive assistant can think and write
- proactive watcher can think and notify

That gives you a system that feels like a personal assistant instead of a command parser, without giving the background process unsafe write power.
