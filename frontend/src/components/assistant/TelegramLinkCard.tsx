import type { TelegramLink, TelegramLinkCode } from '@/types';

function fmt(value: string | null | undefined) {
  if (!value) return null;
  return new Date(value).toLocaleString('es-ES', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function TelegramLinkCard({
  link,
  linkCode,
  loading,
  onGenerateCode,
}: {
  link: TelegramLink | null | undefined;
  linkCode: TelegramLinkCode | null;
  loading: boolean;
  onGenerateCode: () => void;
}) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="section-title mb-2">telegram</p>
          <h3 className="font-serif text-xl text-ink">Conexion del bot</h3>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-mono ${
            link?.is_active
              ? 'bg-emerald-950/40 text-emerald-400'
              : 'bg-surface-3 text-ink-dim'
          }`}
        >
          {link?.is_active ? 'Enlazado' : 'Sin enlazar'}
        </span>
      </div>

      {link?.is_active ? (
        <div className="mt-4 space-y-1 text-sm text-ink-dim">
          <p>Usuario: {link.telegram_username ? `@${link.telegram_username}` : 'sin username'}</p>
          <p>Ultima actividad: {fmt(link.last_seen_at) ?? 'sin actividad'}</p>
        </div>
      ) : (
        <div className="mt-4 space-y-3">
          <p className="text-sm text-ink-dim">
            Genera un codigo y envialo al bot con <span className="font-mono text-ink">/start CODIGO</span>.
          </p>
          <button type="button" onClick={onGenerateCode} disabled={loading} className="btn-primary disabled:opacity-50">
            {loading ? 'Generando…' : 'Generar codigo'}
          </button>
          {linkCode && (
            <div className="rounded-lg border border-amber/30 bg-amber/10 px-4 py-3">
              <p className="text-xs font-mono uppercase tracking-widest text-amber">codigo</p>
              <p className="mt-2 font-mono text-lg text-ink">{linkCode.code}</p>
              <p className="mt-2 text-xs text-ink-dim">
                Expira: {fmt(linkCode.expires_at) ?? 'sin fecha'}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
