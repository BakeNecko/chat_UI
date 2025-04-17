import React, { useState } from 'react';
import { 
    Box,
    Heading, 
    Button,
} from '@chakra-ui/react';
import { useQuery } from '@tanstack/react-query';
import { ChatService, MyChatsResponse, UserShort } from '@/client';
import Chat from './Chat';
import CreateChat from './ChatCreate';

const ListChats: React.FC = () => {
    const [selectedChat, setSelectedChat] = useState<{
        type: string;
        chatId: number;
        users: UserShort[];
        chatName: string;
        receiverId: string | number;
        currentUserId: number;
    } | null>(null);
    
    const [isCreateChatOpen, setIsCreateChatOpen] = useState(false);
    
    const currentUserId = Number(localStorage.getItem("userId"));

    const { data: myChats, error, isLoading, refetch } = useQuery<MyChatsResponse, Error>({
        queryKey: ['myChats'],
        queryFn: ChatService.getMyChats,
        enabled: !!currentUserId,
    });

    const handleChatClick = (
        chatId: number,
        type: string,
        users: UserShort[],
        chatName: string,
        receiverId: string | number
    ) => {
        setSelectedChat({ type, chatId, users, chatName, receiverId, currentUserId });
    };

    const handleBackClick = () => {
        setSelectedChat(null);
    };

    if (selectedChat) {
        return (
            <Box p={4}>
                <Button onClick={handleBackClick} mb={4}>
                    Назад
                </Button>
                <Chat 
                    type={selectedChat.type} 
                    chatId={selectedChat.chatId} 
                    users={selectedChat.users} 
                    chatName={selectedChat.chatName}
                    receiverId={selectedChat.receiverId}
                    currentUserId={selectedChat.currentUserId}
                />
            </Box>
        );
    }

    if (isLoading) {
        return <Box p={4}>Загрузка...</Box>;
    }

    if (error) {
        return <Box p={4}>Ошибка при получении чатов: {error.message}</Box>;
    }

    return (
      <>
      <Box p={4}>
          <Heading as="h2" size="lg" mb={4}>Мои Чаты</Heading>

          <Button colorScheme="teal" onClick={() => setIsCreateChatOpen(true)} mb={4}>
              Создать чат
          </Button>

          {isCreateChatOpen && (
              <Box
                  position="fixed"
                  top={0}
                  left={0}
                  width="100vw"
                  height="100vh"
                  bg="blackAlpha.600"
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  zIndex={1400}
              >
                  <CreateChat onClose={() => {
                      setIsCreateChatOpen(false);
                      refetch();
                  }} onSuccess={refetch} />
              </Box>
          )}

          <Heading as="h3" size="md" mb={2}>Личные Чаты</Heading>
          {myChats?.lc_chats.map(chat => {
            const otherUser  = chat.users.find(user => Number(user.id) !== Number(currentUserId));
            if (otherUser ) {
                const chatName = `Чат с ${otherUser .full_name || otherUser .email || 'Неизвестный пользователь'}`;
                return (
                    <Button 
                        key={chat.id} 
                        onClick={() => handleChatClick(chat.id, 'lc', chat.users, chatName, otherUser .id)} 
                        width="100%" 
                        mb={2}
                    >
                        {chatName}
                    </Button>
                );
            }
            return null;
          })}

          <Heading as="h3" size="md" mb={2}>Групповые Чаты</Heading>
          {myChats?.group_chats.map(chat => (
              <Button key={chat.id} onClick={() => handleChatClick(chat.id, 'group', chat.users, chat.name, chat.chat_id)} width="100%" mb={2}>
                  {chat.name}
              </Button>
          ))}
      </Box>
      </>
  );
};

export default ListChats;