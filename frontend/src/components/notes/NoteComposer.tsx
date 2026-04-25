import { useState } from 'react';

export default function NoteComposer({
  onCreate,
  loading,
}: {
  onCreate: (payload: { content: string; category: string }) => Promise<void> | void;
  loading: boolean;
}) {
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('general');

  const submit = async () => {
    const next = content.trim();
    if (!next || loading) return;
    await onCreate({ content: next, category: category.trim() || 'general' });
    setContent('');
  };

  return (
    <div className="card p-5">
      <p className="section-title mb-2">nueva nota</p>
      <div className="grid gap-3">
        <input
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          placeholder="Categoria"
          className="rounded-lg border border-border bg-surface-3 px-3 py-2 text-sm text-ink focus:border-amber focus:outline-none"
        />
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={4}
          placeholder="Escribe una nota rapida"
          className="resize-none rounded-lg border border-border bg-surface-3 px-3 py-3 text-sm text-ink placeholder:text-ink-dim focus:border-amber focus:outline-none"
        />
        <div className="flex justify-end">
          <button type="button" onClick={() => void submit()} disabled={loading || !content.trim()} className="btn-primary disabled:opacity-50">
            Guardar nota
          </button>
        </div>
      </div>
    </div>
  );
}
