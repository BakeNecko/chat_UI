import { createFileRoute } from "@tanstack/react-router";
import ChatList from '@/components/Chats/ChatsList';


export const Route = createFileRoute("/_layout/chat_list")({
  component: ChatList,
})
