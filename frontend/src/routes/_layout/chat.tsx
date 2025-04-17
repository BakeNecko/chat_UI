import { createFileRoute } from "@tanstack/react-router";
import Chat from '@/components/Chats/Chat';

export const Route = createFileRoute("/_layout/chat/:type/:chatUuid/:chatId")({
  component: Chat,
});