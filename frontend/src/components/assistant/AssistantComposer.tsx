import { useState } from 'react';

export default function AssistantComposer({
  onSend,
  loading,
}: {
  onSend: (message: string) => Promise<void> | void;
  loading: boolean;
}) {
  const [value, setValue] = useState('');

  const submit = async () => {
    const message = value.trim();
    if (!message || loading) return;
    setValue('');
    await onSend(message);
  };

  return (
    <div className="card p-4">
      <div className="flex flex-col gap-3">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              void submit();
            }
          }}
          rows={3}
          placeholder="Ejemplo: crea tarea llamar al dentista manana"
          className="w-full resize-none rounded-lg border border-border bg-surface-3 px-3 py-3 text-sm text-ink placeholder:text-ink-dim focus:border-amber focus:outline-none"
        />
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-mono text-ink-dim">
            Enter envia. Shift + Enter anade linea.
          </p>
          <button
            type="button"
            onClick={() => void submit()}
            disabled={loading || !value.trim()}
            className="btn-primary disabled:opacity-50"
          >
            Enviar
          </button>
        </div>
      </div>
    </div>
  );
}
