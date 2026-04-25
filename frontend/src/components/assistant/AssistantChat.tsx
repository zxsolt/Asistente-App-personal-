import type { AssistantMessageResponse } from '@/types';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  text: string;
  response?: AssistantMessageResponse;
  status?: 'error';
}

function metaLabel(response?: AssistantMessageResponse) {
  if (!response) return null;
  return [response.intent, response.persistence_mode, response.used_ai ? 'IA' : 'regla'].join(' · ');
}

export default function AssistantChat({
  messages,
  loading,
}: {
  messages: ChatMessage[];
  loading: boolean;
}) {
  return (
    <div className="card min-h-[420px] max-h-[68vh] overflow-y-auto p-4 sm:p-5">
      <div className="space-y-4">
        {messages.map((message) => {
          const isUser = message.role === 'user';
          const isSystem = message.role === 'system';
          const isError = message.status === 'error';

          return (
            <div
              key={message.id}
              className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 border ${
                  isUser
                    ? 'bg-amber text-canvas border-amber'
                    : isSystem
                      ? 'bg-surface-3 text-ink-muted border-border'
                      : isError
                        ? 'bg-red-950/30 text-status-discarded border-red-900/40'
                        : 'bg-surface-2 text-ink border-border'
                }`}
              >
                <p className="whitespace-pre-wrap text-sm leading-6">{message.text}</p>
                {!isUser && message.response && (
                  <>
                    <p className="mt-2 text-[11px] font-mono uppercase tracking-wider text-ink-dim">
                      {metaLabel(message.response)}
                    </p>
                    {message.response.planning_json && (
                      <div className="mt-3 rounded-xl border border-border bg-canvas/50 p-3">
                        <p className="text-[11px] font-mono uppercase tracking-widest text-amber">
                          planner json
                        </p>
                        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-xs leading-5 text-ink-dim">
                          {JSON.stringify(message.response.planning_json, null, 2)}
                        </pre>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          );
        })}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl border border-border bg-surface-2 px-4 py-3 text-sm font-mono text-ink-dim">
              Pensando…
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
