import { Link } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import NoteComposer from '@/components/notes/NoteComposer';
import NoteList from '@/components/notes/NoteList';
import { notesApi } from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import type { Note } from '@/types';

export default function NotesPage() {
  const { data: notes = [], isLoading, error } = useQuery<Note[]>({
    queryKey: ['notes'],
    queryFn: notesApi.list,
  });

  const createNoteMutation = useMutation({
    mutationFn: (payload: { content: string; category: string }) =>
      notesApi.create({ ...payload, source: 'web' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notes'] }),
  });

  return (
    <div className="min-h-screen bg-canvas">
      <div
        className="fixed inset-0 pointer-events-none opacity-[0.025]"
        style={{
          backgroundImage:
            'repeating-linear-gradient(0deg, #ddd8cf 0px, #ddd8cf 1px, transparent 1px, transparent 48px), repeating-linear-gradient(90deg, #ddd8cf 0px, #ddd8cf 1px, transparent 1px, transparent 48px)',
        }}
      />

      <header className="sticky top-0 z-20 bg-canvas/85 backdrop-blur-md border-b border-border">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-ink-muted hover:text-ink font-mono text-sm transition-colors">
              ← Inicio
            </Link>
            <div className="w-px h-4 bg-border" />
            <span className="font-serif text-lg text-ink">Notas</span>
          </div>
          <nav className="flex items-center gap-1">
            <Link to="/assistant" className="tab-btn">Asistente</Link>
            <Link to="/notes" className="tab-btn active">Notas</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10 animate-fade-in">
        <div className="mb-8">
          <p className="section-title mb-1">captura rapida</p>
          <h1 className="font-serif text-3xl text-ink">Notas personales</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-ink-dim">
            Aqui ves las notas creadas desde web y las que el asistente vaya guardando desde otros canales.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[320px,minmax(0,1fr)]">
          <NoteComposer
            onCreate={async (payload) => createNoteMutation.mutateAsync(payload)}
            loading={createNoteMutation.isPending}
          />
          <div>
            {isLoading ? (
              <div className="card p-8 text-center text-sm font-mono text-ink-dim">Cargando notas…</div>
            ) : error ? (
              <div className="card border-red-900/40 bg-red-950/20 p-8 text-sm font-mono text-status-discarded">
                No se pudieron cargar las notas.
              </div>
            ) : (
              <NoteList notes={notes} />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
