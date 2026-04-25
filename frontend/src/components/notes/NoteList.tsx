import type { Note } from '@/types';

function fmt(value: string) {
  return new Date(value).toLocaleString('es-ES', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function NoteList({ notes }: { notes: Note[] }) {
  if (notes.length === 0) {
    return (
      <div className="card p-8 text-center">
        <p className="font-mono text-sm text-ink-dim">Todavia no hay notas.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {notes.map((note) => (
        <article key={note.id} className="card p-5">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-surface-3 px-2.5 py-1 text-[11px] font-mono uppercase tracking-wider text-amber">
              {note.category}
            </span>
            <span className="text-xs font-mono text-ink-dim">{note.source}</span>
            <span className="text-xs font-mono text-ink-dim">{fmt(note.created_at)}</span>
          </div>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-ink">{note.content}</p>
        </article>
      ))}
    </div>
  );
}
