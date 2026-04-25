import type { AssistantNotification } from '@/types';

function fmt(value: string | null | undefined) {
  if (!value) return null;
  return new Date(value).toLocaleString('es-ES', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function AssistantNotificationsPanel({
  notifications,
  loading,
  onMarkRead,
}: {
  notifications: AssistantNotification[];
  loading: boolean;
  onMarkRead: (notificationId: number) => void;
}) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="section-title mb-2">proactivo</p>
          <h3 className="font-serif text-xl text-ink">Avisos del asistente</h3>
        </div>
        <span className="rounded-full bg-surface-3 px-3 py-1 text-xs font-mono text-ink-dim">
          {loading ? 'cargando' : `${notifications.length} avisos`}
        </span>
      </div>

      <div className="mt-4 space-y-3">
        {notifications.length === 0 && (
          <p className="text-sm text-ink-dim">
            Aun no hay avisos. El watcher empezara por recordatorios cercanos, dias vacios y tareas atascadas.
          </p>
        )}

        {notifications.map((notification) => (
          <article
            key={notification.id}
            className={`rounded-2xl border px-4 py-3 ${
              notification.read_at
                ? 'border-border bg-surface-3/50'
                : 'border-amber/30 bg-amber/10'
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-mono uppercase tracking-widest text-amber">
                  {notification.kind}
                </p>
                <h4 className="mt-1 text-sm font-semibold text-ink">{notification.title}</h4>
              </div>
              {!notification.read_at && (
                <button type="button" onClick={() => onMarkRead(notification.id)} className="tab-btn">
                  Marcar leido
                </button>
              )}
            </div>
            <p className="mt-2 text-sm leading-6 text-ink-dim">{notification.message}</p>
            <p className="mt-3 text-[11px] font-mono uppercase tracking-wider text-ink-dim">
              {notification.channel_targets.join(' + ')} · {fmt(notification.created_at) ?? 'sin fecha'}
              {notification.last_error ? ` · ${notification.last_error}` : ''}
            </p>
          </article>
        ))}
      </div>
    </div>
  );
}
