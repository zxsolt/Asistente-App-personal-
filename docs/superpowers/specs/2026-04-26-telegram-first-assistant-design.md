# Telegram-First Personal Assistant Design

## Goal

Refocus the current product from a planner-centric app into a personal assistant centered on Telegram, with the existing web application kept only as a secondary support panel.

The assistant should feel like a real assistant, not a command parser. It should:

- use the database as persistent memory
- focus only on tasks, reminders, and notes
- act when it has enough information
- ask one short clarification when information is missing
- avoid creating garbage records from meta-intent phrases

## Product Direction

### Primary interface

Telegram becomes the primary interface.

The user should be able to manage personal organization mainly by chatting naturally with the assistant in Telegram.

### Secondary interface

The existing web app remains available, but only as a support surface for:

- authentication
- Telegram link management
- reviewing tasks, reminders, notes, and notifications
- debugging or inspecting assistant behavior

The web UI is no longer the center of the product.

## Scope

This redesign focuses only on:

- tasks
- reminders
- notes
- Telegram-first assistant behavior
- minimal supporting web panel

This redesign explicitly excludes for now:

- fitness
- planner-heavy weekly workflows
- voice and Whisper
- broad general-purpose chat
- complex autonomous replanning

## Core Product Behavior

The assistant must classify each incoming message into one of four decision outcomes:

1. `act`
   enough information is available, so the assistant writes or updates data directly
2. `answer`
   the user is asking for information and the assistant should respond from memory or reasoning
3. `clarify`
   the request is valid but incomplete, so the assistant asks exactly one short question
4. `proactive_notify`
   only for the separate watcher, which reads the database and sends useful reminders or alerts

The key rule is:

- if the user expresses only meta-intent, the assistant must not write anything
- it should ask one short clarification instead

Examples:

- `quiero crear una tarea` -> `¿Que tarea?`
- `añademe un recordatorio` -> `¿De que y para cuando?`
- `mañana estudiar python` -> act directly if confidence is high
- `que tengo hoy` -> answer directly

## Architectural Shift

The current assistant flow is too rigid because it depends on early intent classification and direct execution.

This redesign replaces that with a new core pipeline:

1. `understanding`
   identify the real user goal, the actionable object, and any missing fields
2. `policy`
   decide whether to act, answer, or ask one short clarification
3. `tools`
   execute safe application-level operations against tasks, reminders, and notes
4. `memory`
   load prioritized context from the database
5. `response generation`
   produce a direct natural-language reply in Spanish

This is still tool-based and controlled. It is not a freeform agent with arbitrary write access.

## Understanding Layer

Introduce a structured understanding result produced for every inbound Telegram or web assistant message.

Suggested structure:

- `goal`
  create_task, update_task, query_tasks, create_reminder, create_note, query_memory, unknown
- `actionable_object`
  the actual task, reminder, or note content if present
- `time_context`
  parsed time information if present
- `missing_fields`
  required fields that are still absent
- `confidence`
  normalized confidence score
- `should_write`
  whether the assistant is allowed to write immediately

Examples:

### `quiero crear una tarea`

- `goal`: create_task
- `actionable_object`: null
- `missing_fields`: [task_content]
- `should_write`: false

### `recuerdame en 10 minutos llamar a mi padre`

- `goal`: create_reminder
- `actionable_object`: llamar a mi padre
- `time_context`: in 10 minutes
- `missing_fields`: []
- `should_write`: true

### `que tengo hoy`

- `goal`: query_tasks
- `actionable_object`: null
- `missing_fields`: []
- `should_write`: false

## Policy Layer

The policy layer determines the assistant's next step from the understanding result and memory context.

### Write policy

The assistant may write when all of these are true:

- the goal is clear
- required fields are present
- confidence is above the configured threshold
- the action is one of the allowed safe tools

### Clarification policy

The assistant asks one short question when:

- the goal is valid but incomplete
- the content is meta-intent instead of real content
- time or task details are missing

Clarification rules:

- exactly one short question
- no multi-question replies
- no long explanations unless the user asks for them

### Answer policy

The assistant answers directly when the message is primarily a query over memory, such as:

- `que tengo hoy`
- `que tareas tengo esta semana`
- `que notas guarde ayer`

## Tool Layer

The assistant must interact with the database only through explicit application tools.

Initial tool set:

- `create_task`
- `list_tasks`
- `update_task`
- `complete_task`
- `create_reminder`
- `list_reminders`
- `create_note`
- `list_notes`

Tool rules:

- no arbitrary SQL
- no destructive bulk deletion
- no mass rewrites
- no silent historical cleanup

## Memory Layer

The assistant should continue using the database as memory, but narrowed to the new product focus.

Relevant memory domains:

- active tasks
- pending reminders
- recent notes
- recent task completions
- relevant historical items for continuity

Prioritization strategy:

1. active context
2. recent context
3. relevant historical context on demand

The assistant should not drag in unrelated planner complexity unless needed for a query.

## Telegram-First Flow

Telegram becomes the main runtime surface.

Inbound message flow:

1. Telegram update received
2. user resolved through link
3. understanding layer parses message
4. memory layer loads relevant context
5. policy chooses act, answer, or clarify
6. tool execution happens if needed
7. direct natural-language reply is sent back to Telegram

The reply style should be:

- concise
- direct
- useful
- not verbose

## Web Support Panel

The web app should be simplified in product meaning, not necessarily rewritten immediately.

Its role becomes:

- show assistant notifications
- show tasks, reminders, and notes
- allow Telegram linking
- allow manual review of assistant-created data

The web assistant page can remain, but Telegram is the main path the product is optimized for.

## Proactive Watcher

Keep the proactive watcher introduced in the previous design direction, but frame it around Telegram-first usage.

Rules:

- read-only over planner/task/reminder/note data
- may create assistant notifications
- may send notifications to Telegram and web
- may not create or edit tasks, notes, or reminders by itself

Initial proactive use cases:

- due reminder
- no plan for today
- stale task
- current week nearly empty
- simple follow-up hint

## Data Model

Existing models reused:

- `full_tasks`
- `reminders`
- `notes`
- `telegram_links`
- `assistant_notifications`

No major new planner entities are required for this redesign. The focus is behavioral rather than schema-heavy.

## Backend Changes

### New core services

Add or refactor toward these components:

- `assistant/understanding_service.py`
- `assistant/policy_service.py`
- `assistant/tool_registry.py`
- `assistant/memory_service.py`
- `assistant/telegram_orchestrator.py`

### Existing services to adapt

- `assistant/service.py`
  becomes orchestration glue instead of a rigid classifier-first executor
- `telegram/service.py`
  becomes the main channel adapter for the assistant
- `planner/context_service.py`
  gets narrowed or wrapped for the assistant memory use case

## Frontend Changes

Keep frontend changes modest for this phase.

Required changes:

- improve the assistant page so it reflects act/answer/clarify outcomes cleanly
- keep notification feed visible
- keep Telegram linking prominent
- de-emphasize planner-heavy interactions

## Error Handling

### Assistant behavior

- if understanding confidence is too low, ask one short clarification
- if a tool call fails, return a direct failure message without partial destructive behavior
- if AI reasoning is unavailable, fall back to minimal safe clarification or query behavior

### Telegram behavior

- if the Telegram user is not linked, ask them to link first
- if outbound Telegram send fails, log and keep notification state for inspection

## Testing Strategy

### Unit tests

- meta-intent detection
- missing field detection
- short clarification generation
- write vs no-write policy decisions
- reminder parsing and creation

### Integration tests

- Telegram task creation flow
- Telegram reminder creation flow
- Telegram note creation flow
- ambiguous request -> one short clarification -> no DB write
- memory query -> answer from DB

### Regression tests

- existing auth still works
- Telegram linking still works
- notes/reminders routes remain valid
- proactive watcher continues working

## Rollout Plan

### Phase 1

- introduce understanding result and policy layer
- stop writing literal meta-intent phrases to the database
- make Telegram the most reliable path
- ensure one short clarification behavior

### Phase 2

- refactor web assistant page around the new backend behavior
- tighten memory retrieval for queries
- improve follow-up handling and continuity

### Phase 3

- prune planner-first UX from the product surface if it becomes noise
- keep only the support panel needed for inspection and trust

## Recommendation

Do not keep patching the current classifier-first assistant. Replace the assistant core with a Telegram-first architecture based on:

- understanding
- policy
- tools
- memory

That is the smallest redesign that actually matches the product you described: a personal assistant with an intelligent database, not a brittle planning app with chat bolted on top.
