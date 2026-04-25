# Assistant Frontend Phase 2 Design

## Goal

Extend the existing React planner frontend with the first visible assistant-facing UI layer, without replacing the current weekly planning workflows.

This phase delivers:

- a new assistant chat page
- a new notes page
- small task UI upgrades to show assistant metadata
- navigation updates that expose the new backend capabilities already added in Phase 1

This phase does not deliver:

- Telegram UI management beyond link status and code generation
- audio recording and transcription UI
- fitness pages
- a large visual redesign of the existing planner

## Constraints

- Keep the current planner flows intact
- Reuse the existing React Router structure
- Reuse the current API client layer in `frontend/src/lib/api.ts`
- Preserve the established visual language already present in the app
- Keep the UI simple and production-usable rather than experimental

## Existing Frontend Context

The current frontend already has:

- authentication flow
- `HomePage` with week list
- `WeekPage` with planner tabs
- a shared API layer using Axios
- React Query for data loading and mutations

The UI style is already defined and should be preserved:

- paper-like background
- serif headers
- mono secondary labels
- card-based content sections

## Phase 2 Scope

### Included

- Add route `/assistant`
- Add route `/notes`
- Add header navigation entry points from the existing app shell
- Add assistant API client methods
- Add notes API client methods
- Show task `priority` and `due_at` when present
- Show Telegram link status and allow link-code generation from the assistant page

### Excluded

- reminders page
- fitness page
- audio recording controls
- streaming chat
- full conversation persistence in backend

## Route Design

## `/assistant`

Purpose:

- provide the first web UI for the backend assistant flow
- let the user test the assistant without Telegram
- expose Telegram link status and link-code generation

Main sections:

- page header
- Telegram connection card
- chat conversation panel
- composer input

Behavior:

- user types a message
- frontend calls `POST /assistant/message`
- assistant reply is appended to local chat history
- loading and error states are rendered inline

Conversation persistence in Phase 2 is client-local only. It should survive component re-renders but not require backend chat history yet.

## `/notes`

Purpose:

- provide a visible UI for the notes capability already available in the backend

Main sections:

- page header
- compact create-note form
- notes list ordered by newest first

Behavior:

- list notes from `GET /notes/`
- create note with `POST /notes/`
- invalidate and refresh list after mutation

## Planner Task UI Upgrade

The current planner task cards should be extended in a minimal way:

- if `due_at` exists, show it in the header or metadata row
- if `priority` exists, show a small badge

No planner workflow changes are required in this phase. The goal is visibility of assistant-created metadata, not a task UX redesign.

## API Integration

## New client methods

In `frontend/src/lib/api.ts`, add:

- `assistantApi.sendMessage`
- `notesApi.list`
- `notesApi.create`
- `telegramApi.getLink`
- `telegramApi.createLinkCode`

The assistant page will use:

- `assistantApi.sendMessage`
- `telegramApi.getLink`
- `telegramApi.createLinkCode`

The notes page will use:

- `notesApi.list`
- `notesApi.create`

## Type Layer

Extend `frontend/src/types/index.ts` with:

- `AssistantMessageRequest`
- `AssistantMessageResponse`
- `Note`
- `TelegramLink`
- task shape extensions for `priority` and `due_at`

## Component Design

## Assistant Page Components

Recommended component split:

- `pages/AssistantPage.tsx`
- `components/assistant/AssistantChat.tsx`
- `components/assistant/AssistantComposer.tsx`
- `components/assistant/TelegramLinkCard.tsx`

Responsibilities:

- page component owns queries and mutations
- chat component renders messages
- composer handles message input and submit
- Telegram card renders link status and code actions

## Notes Page Components

Recommended component split:

- `pages/NotesPage.tsx`
- `components/notes/NoteComposer.tsx`
- `components/notes/NoteList.tsx`

This keeps the page readable and avoids putting all query and form logic in a single component.

## State Management

Phase 2 should keep state management local and simple:

- React Query for server state
- local component state for chat transcript and composer value

No new global Zustand store is required yet.

## UX Decisions

## Assistant UI

The chat should feel integrated with the app, not like a different product.

Design direction:

- same background and typography system as existing pages
- card-like chat thread area
- distinct user and assistant bubbles
- compact inline metadata for `intent` or `used_ai` only if useful

Recommended behavior:

- optimistic append of the user message
- assistant response appended after mutation resolves
- error row appended if request fails

## Telegram Linking UX

The assistant page should show:

- current Telegram link state if linked
- a button to generate a link code if not linked
- the generated code and expiration timestamp

This gives the user a complete bridge from web to Telegram without needing a separate settings page.

## Notes UI

The notes page should stay fast and compact:

- textarea or single multiline field
- category field left simple
- note cards with category, source, and timestamp

## Error Handling

The UI should handle:

- assistant request failure
- notes load failure
- Telegram link-code generation failure

Errors should render as inline cards or compact banners, not browser alerts.

## Testing Strategy

Phase 2 should be validated with:

- successful chat request through `/assistant/message`
- successful note creation and list refresh
- successful Telegram link-code generation
- task metadata rendering for `priority` and `due_at`

At minimum, the implementation should be manually smoke-tested in the running app.

## Risks

- chat transcript stored only locally means no cross-device continuity yet
- assistant replies may vary in shape over time, so response rendering should stay tolerant
- adding top-level navigation must avoid cluttering the current planner entry flow

## Recommendation

Implement this phase as a visible but conservative extension of the current app:

- add assistant and notes pages
- expose Telegram linking in the assistant page
- surface assistant task metadata inside the existing planner

This creates the first user-facing layer for the new assistant platform while keeping the current planner stable and familiar.
