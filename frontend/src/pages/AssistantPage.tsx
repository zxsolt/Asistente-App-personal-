import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import AssistantChat, { type ChatMessage } from '@/components/assistant/AssistantChat';
import AssistantComposer from '@/components/assistant/AssistantComposer';
import AssistantNotificationsPanel from '@/components/assistant/AssistantNotificationsPanel';
import TelegramLinkCard from '@/components/assistant/TelegramLinkCard';
import { assistantApi, telegramApi } from '@/lib/api';
import type { AssistantMessageResponse, AssistantNotification, TelegramLinkCode } from '@/types';

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: 'welcome',
    role: 'system',
    text: 'Prueba mensajes como “crea tarea llamar al dentista manana”, “que tengo hoy” o “apunta nota comprar straps para gym”.',
  },
];

export default function AssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [linkCode, setLinkCode] = useState<TelegramLinkCode | null>(null);
  const queryClient = useQueryClient();

  const { data: telegramLink, isLoading: linkLoading } = useQuery({
    queryKey: ['telegram-link'],
    queryFn: telegramApi.getLink,
  });

  const { data: notifications = [], isLoading: notificationsLoading } = useQuery<AssistantNotification[]>({
    queryKey: ['assistant-notifications'],
    queryFn: assistantApi.listNotifications,
    refetchInterval: 30000,
  });

  const sendMessageMutation = useMutation({
    mutationFn: (message: string) =>
      assistantApi.sendMessage({ message, channel: 'web' }),
  });

  const linkCodeMutation = useMutation({
    mutationFn: telegramApi.createLinkCode,
    onSuccess: (data) => setLinkCode(data),
  });

  const markReadMutation = useMutation({
    mutationFn: assistantApi.markNotificationRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assistant-notifications'] });
    },
  });

  const sending = sendMessageMutation.isPending;
  const generatingCode = linkCodeMutation.isPending || linkLoading;

  const transcript = useMemo(() => messages, [messages]);

  const handleSend = async (message: string) => {
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: message,
    };
    setMessages((current) => [...current, userMessage]);

    try {
      const response: AssistantMessageResponse = await sendMessageMutation.mutateAsync(message);
      queryClient.invalidateQueries({ queryKey: ['assistant-notifications'] });
      setMessages((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          text: response.reply_text,
          response,
        },
      ]);
    } catch (error: any) {
      const detail = error?.response?.data?.detail ?? 'No se pudo enviar el mensaje al asistente.';
      setMessages((current) => [
        ...current,
        {
          id: `assistant-error-${Date.now()}`,
          role: 'assistant',
          text: String(detail),
          status: 'error',
        },
      ]);
    }
  };

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
            <span className="font-serif text-lg text-ink">Asistente</span>
          </div>
          <nav className="flex items-center gap-1">
            <Link to="/assistant" className="tab-btn active">Asistente</Link>
            <Link to="/notes" className="tab-btn">Notas</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10 animate-fade-in">
        <div className="grid gap-6 lg:grid-cols-[320px,minmax(0,1fr)]">
          <div className="space-y-6">
            <div>
              <p className="section-title mb-1">capa visible</p>
              <h1 className="font-serif text-3xl text-ink">Asistente web</h1>
              <p className="mt-3 max-w-sm text-sm leading-6 text-ink-dim">
                Usa el mismo backend del asistente para probar tareas, consultas y notas sin pasar por Telegram.
              </p>
            </div>
            <TelegramLinkCard
              link={telegramLink}
              linkCode={linkCode}
              loading={generatingCode}
              onGenerateCode={() => linkCodeMutation.mutate()}
            />
            <AssistantNotificationsPanel
              notifications={notifications}
              loading={notificationsLoading}
              onMarkRead={(notificationId) => markReadMutation.mutate(notificationId)}
            />
          </div>

          <div className="space-y-4">
            <AssistantChat messages={transcript} loading={sending} />
            <AssistantComposer onSend={handleSend} loading={sending} />
          </div>
        </div>
      </main>
    </div>
  );
}
