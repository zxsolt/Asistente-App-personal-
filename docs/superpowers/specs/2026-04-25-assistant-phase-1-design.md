# Assistant Phase 1 Design

## Goal

Extend the existing weekly planner backend into the first production-ready slice of a personal assistant platform without breaking the current React frontend or FastAPI planner flows.

Phase 1 delivers:

- assistant core in the existing backend
- Telegram text integration
- OpenRouter integration
- notes and reminders persistence
- task extensions for assistant-driven creation and querying
- reusable contracts for future web chat, voice, and fitness modules

Phase 1 explicitly does not deliver:

- Telegram audio ingestion
- Whisper transcription
- fitness routines and sessions
- new frontend views
- full PostgreSQL migration

The default database remains the current SQLite-backed setup in Phase 1, with service boundaries chosen so a later PostgreSQL migration does not require rewriting assistant flows.

## Constraints

- Keep the current planner application functional
- Reuse existing task and auth models where practical
- Avoid rewrites of current planner routes
- Add new modules behind clear service boundaries
- Keep the system deployable in the current Coolify-oriented Docker setup
- Prefer deterministic logic before AI calls

## Existing System Context

The current application has:

- FastAPI backend with SQLAlchemy async models and routers
- React frontend for weekly planning
- task-oriented planner entities already persisted in the database
- simple Docker deployment using a single container with Nginx + FastAPI

This phase builds on the existing backend by adding assistant-specific modules under the current `backend/app` package.

## Phase 1 Scope

### Included

- New backend modules:
  - `app/assistant`
  - `app/ai`
  - `app/telegram`
  - `app/notes`
  - `app/reminders`
- Extensions to task persistence and task service logic
- Assistant endpoint usable by future frontend chat
- Telegram webhook flow for text messages
- Context-aware OpenRouter prompts
- Structured logging and error handling for the new modules

### Excluded

- Audio upload and transcription
- Fitness data model and APIs
- New React assistant, notes, or fitness pages
- Advanced recurring reminder scheduling worker
- Cost dashboards or model analytics UI

## Architecture Overview

Phase 1 adds a backend-only assistant layer with a clean flow:

1. Input arrives from Telegram or a future web client
2. Transport layer normalizes the message into a common assistant request
3. Assistant classifier identifies the likely intent
4. Router attempts deterministic action execution
5. If deterministic execution is insufficient, assistant builds database context and calls OpenRouter
6. Result is persisted when needed and formatted back to the source channel

### Logical Modules

#### `app/telegram`

Responsibilities:

- receive Telegram webhook updates
- validate source user linkage
- normalize inbound text updates
- send responses back through Telegram Bot API

Phase 1 supports text messages only.

#### `app/assistant`

Responsibilities:

- define assistant request and response contracts
- classify intent
- route actions
- gather dynamic context from services
- orchestrate deterministic logic and AI fallback

Subcomponents:

- `classifier.py`
- `router.py`
- `service.py`
- `schemas.py`
- `formatters.py`

#### `app/ai`

Responsibilities:

- provide a centralized OpenRouter client
- manage model selection through configuration
- build prompts from assistant context
- isolate provider-specific request and response logic

Subcomponents:

- `client.py`
- `prompts.py`
- `schemas.py`
- `service.py`

#### `app/notes`

Responsibilities:

- create and query notes
- store origin metadata
- expose note retrieval for assistant context building

#### `app/reminders`

Responsibilities:

- persist reminders
- expose reminder queries to the assistant
- provide an extensible base for future recurrence handling

#### Existing task modules

Responsibilities remain intact, but Phase 1 extends tasks with assistant-facing metadata and query helpers.

## Data Design

### Existing Tables Reused

- `users`
- existing weekly planning tables, especially task-related entities

The assistant should reuse current task records instead of creating a parallel task table.

### Existing Table Extensions

The current task model should be extended with fields that enable assistant-driven workflows:

- `priority`: enum-like string such as `low`, `medium`, `high`
- `due_at`: nullable datetime for direct date-based querying
- `source`: nullable string such as `web`, `telegram`, `assistant`
- `source_ref`: nullable external reference such as Telegram message id
- `natural_language_input`: nullable raw text used to create the task

These additions preserve compatibility with the weekly planner while letting the assistant answer time-based questions like "what do I have today".

### New Tables

### `notes`

Core fields:

- `id`
- `user_id`
- `content`
- `category` such as `general`, `task_context`, `fitness`, `idea`
- `source`
- `source_ref`
- `created_at`
- `updated_at`

### `reminders`

Core fields:

- `id`
- `user_id`
- `title`
- `description`
- `scheduled_for`
- `recurrence_rule` nullable string
- `status` such as `pending`, `sent`, `cancelled`
- `source`
- `source_ref`
- `created_at`
- `updated_at`

### `telegram_links`

Core fields:

- `id`
- `user_id`
- `telegram_chat_id`
- `telegram_user_id`
- `telegram_username`
- `is_active`
- `last_seen_at`
- `created_at`
- `updated_at`

This table decouples Telegram identity from the existing user model and allows future support for re-linking or multiple channels.

### Service Layer Boundaries

The assistant must not query ORM models ad hoc from every module. Instead, Phase 1 should introduce service-level access patterns:

- `TaskQueryService`
- `NoteService`
- `ReminderService`
- `TelegramLinkService`
- `AssistantContextService`

These services expose stable methods such as:

- `get_tasks_for_today(user_id)`
- `get_tasks_for_range(user_id, start, end)`
- `create_task_from_assistant(user_id, payload)`
- `create_note_from_assistant(user_id, payload)`
- `get_recent_notes(user_id, limit)`
- `get_active_reminders(user_id)`
- `build_context_bundle(user_id, request)`

This isolates query logic and makes later migration to PostgreSQL lower-risk.

## Assistant Logic

### Request Contract

All assistant-capable channels should normalize to a shared request model:

- `user_id`
- `channel` such as `telegram` or `web`
- `message`
- `message_id` optional
- `received_at`
- `metadata` optional dict

### Intent Set

Phase 1 classifier supports:

- `task_create`
- `task_query`
- `note_create`
- `reminder_create`
- `general_query`
- `unknown`

### Classification Strategy

Use a lightweight layered strategy:

1. rule-based detection for obvious commands and phrases
2. entity extraction for dates and priorities when phrasing is simple
3. AI fallback only when intent remains ambiguous

Examples:

- "crea tarea llamar al dentista mañana" -> `task_create`
- "que tengo hoy" -> `task_query`
- "apunta nota comprar straps para gym" -> `note_create`
- "recuerdame pagar autonomos el lunes" -> `reminder_create`

### Router Behavior

The router should attempt deterministic handling first:

- task creation
- date-range task query
- note persistence
- reminder creation

AI should be used when:

- intent is ambiguous
- user asks for a summary or interpretation
- user asks a question that requires synthesized context across modules

## AI Integration

### OpenRouter Requirements

Phase 1 must use OpenRouter as the only LLM gateway.

Configuration fields:

- `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL`
- `OPENROUTER_DEFAULT_MODEL`
- `OPENROUTER_FALLBACK_MODEL` optional
- `OPENROUTER_MAX_INPUT_CHARS`

### Prompt Construction

Prompts should be assembled from:

- system prompt with assistant role and safety boundaries
- user request text
- relevant structured context from the database
- optional action hints from the classifier

The prompt builder must keep context narrow and relevant. For example, a "what do I have today" request should include only today’s tasks and active reminders, not all historical data.

### Cost Control

Phase 1 cost control is basic but explicit:

- deterministic logic before AI
- cap prompt size
- use a configured default model
- allow fallback model for degraded mode
- log model usage and request type

## Telegram Integration

### Delivery Mode

Phase 1 should use Telegram webhook mode, because it fits the current deployed backend model better than long polling.

New route:

- `POST /telegram/webhook`

Responsibilities:

- validate update structure
- ignore unsupported event types
- resolve linked application user
- hand off text content to the assistant service
- send response message back to Telegram

### User Linking

Phase 1 assumes a simple admin-controlled or token-based linking flow. The minimal version can be:

- backend generates a short-lived link code
- user sends the code in Telegram
- backend creates or updates `telegram_links`

The full UX can be improved in later phases.

## API Design

### New Routes

- `POST /assistant/message`
- `POST /telegram/webhook`
- `POST /notes/`
- `GET /notes/`
- `POST /reminders/`
- `GET /reminders/`

### Route Purpose

### `POST /assistant/message`

Primary internal and future web-chat entrypoint.

Request:

- `message`
- `channel`
- authenticated `user_id` derived from the current app user when called from web or internal backend flows
- optional metadata

Response:

- `reply_text`
- `intent`
- `action_taken`
- `entities`
- `used_ai`

This endpoint allows testing the assistant independently from Telegram.

### `POST /telegram/webhook`

Receives Telegram updates and delegates to the assistant service.

### `POST /notes/` and `GET /notes/`

Expose note management for both assistant use and future frontend views.

### `POST /reminders/` and `GET /reminders/`

Expose reminders persistence and retrieval.

## Logging and Error Handling

Phase 1 should introduce structured logs for the assistant path:

- inbound channel
- normalized user id
- intent
- action taken
- whether AI was used
- chosen model
- execution duration
- failure class

Errors should be separated into:

- validation errors
- integration errors such as Telegram or OpenRouter failures
- business logic errors
- unexpected internal errors

Telegram-facing responses should remain user-readable even if upstream AI fails.

## Deployment Impact

Current Docker and Coolify deployment can remain in place for Phase 1.

New environment variables will be required:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET` if used
- `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL`
- `OPENROUTER_DEFAULT_MODEL`
- `OPENROUTER_FALLBACK_MODEL` optional

No deploy topology change is required in Phase 1.

## Testing Strategy

Phase 1 should include:

- unit tests for classifier and router behavior
- service tests for notes, reminders, and task assistant helpers
- API tests for `/assistant/message`
- webhook tests with Telegram update fixtures
- mocked OpenRouter client tests

The highest-value integration test is:

1. send assistant message
2. classify as task creation
3. persist task with parsed due date and metadata
4. return confirmation response

## Risks

- Current data model may mix weekly planner semantics with assistant-wide task semantics
- Relative date parsing can become inconsistent without a dedicated helper
- Telegram user-linking can create support friction if the flow is too manual
- SQLite is acceptable for Phase 1 personal use, but the assistant feature set increases the pressure to migrate later

## Follow-Up Phases

### Phase 2

- Whisper audio ingestion
- Telegram audio support
- transcription-to-assistant flow

### Phase 3

- fitness routines and session tracking
- fitness-aware assistant context

### Phase 4

- React assistant chat view
- notes and reminders pages
- fitness pages

## Recommendation

Implement Phase 1 exactly as the backend foundation for the broader assistant platform. It adds the highest-leverage capabilities first, keeps the current planner stable, and creates reusable contracts for voice, fitness, and frontend chat without forcing a risky rewrite.
