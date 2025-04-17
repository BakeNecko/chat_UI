import React, { useEffect, useState } from 'react';
import moment from 'moment';
import 'moment/locale/ru'; 
import { Box, Heading, Textarea, Button, VStack, HStack, Text } from '@chakra-ui/react';
import { ChatService, ChatMsgResponse, UserShort } from '@/client';
import { useWebSocket } from '../../context/ws_chat_ctx';
import { useQuery } from '@tanstack/react-query';

interface ChatProps {
    type: string;
    chatId: number;
    users: UserShort[];
    chatName: string;
    receiverId: string | number;
    currentUserId: string | number;
}

const Chat: React.FC<ChatProps> = ({ type, chatId, users, chatName, receiverId, currentUserId }) => {
    const [newMessageContent, setNewMessageContent] = useState<string>('');
    const [hoveredMessageId, setHoveredMessageId] = useState<string | null>(null);
    const [showUsers, setShowUsers] = useState<boolean>(false);
    const [isSending, setIsSending] = useState<boolean>(false);
    const [messages, setMessages] = useState<ChatMsgResponse[]>([]);
    const { sendMessage, subscribeToMessages, unsubscribeFromMessages, notifications } = useWebSocket();

    const { refetch: refetchMessages } = useQuery<ChatMsgResponse[], Error>({
        queryKey: ['chatHistory', chatId],
        queryFn: async () => {
            const response = await ChatService.getChatHistory({ chatID: chatId });
            setMessages(response);
            return response;
        },
        enabled: !!chatId,
        refetchOnWindowFocus: false,
    });

    useEffect(() => {
        const messageHandler = (newMessage: ChatMsgResponse) => {
            if (newMessage.chat_id === chatId) {
                if (newMessage.sender_id !== currentUserId) {
                    ChatService.markReadMsg({ 'msgID': newMessage.id });
                }
                refetchMessages();
            }
        };

        subscribeToMessages(messageHandler);

        return () => {
            unsubscribeFromMessages(messageHandler);
        };
    }, [chatId, currentUserId, subscribeToMessages, unsubscribeFromMessages, refetchMessages]);

    useEffect(() => {
        // Обработка уведомлений
        notifications.forEach(notification => {
            if (notification.meta_data && notification.meta_data.who_read) {
                const userIdWhoRead = notification.meta_data.who_read.id;

                // Найти сообщение в локальном состоянии
                setMessages(prevMessages =>
                    prevMessages.map(msg => {
                        if (msg.id === notification.meta_data.msg_id) {
                            // Добавление пользователя в read_by_users
                            return {
                                ...msg,
                                read_by_users: [...(msg.read_by_users || []), userIdWhoRead],
                            };
                        }
                        return msg;
                    })
                );
            }
        });
    }, [notifications]);


    const handleSendMessage = async () => {
        if (!newMessageContent.trim() || isSending) return;

        setIsSending(true);

        try {
            await sendMessage(newMessageContent.trim(), type, receiverId);
            setNewMessageContent('');
            refetchMessages();
        } catch (error) {
            console.error('Ошибка при отправке сообщения:', error);
        } finally {
            setIsSending(false);
        }
    };

    const handleRefreshChat = async () => {
        await refetchMessages();
    };
    
    return (
        <Box p={4}>
            <Heading as="h2" size="lg" mb={4}>{chatName}</Heading>
            {type === 'group' && (
                <Box mb={4}>
                    <Button onClick={() => setShowUsers(!showUsers)} mb={2}>
                        {showUsers ? 'Скрыть пользователей' : 'Показать пользователей чата'}
                    </Button>
                    {showUsers && (
                        <Box
                            borderWidth={1}
                            borderRadius="md"
                            p={4}
                            mt={4}
                            bg="gray.50"
                            boxShadow="sm"
                        >
                            <Heading as="h4" size="md" mb={3} color="teal.600" letterSpacing="wide">
                                Участники чата:
                            </Heading>
                            {users.length > 0 ? (
                                users.map(user => (
                                    <Text
                                        key={user.id}
                                        mb={2}
                                        px={3}
                                        py={1}
                                        bg="white"
                                        borderRadius="md"
                                        boxShadow="xs"
                                        style={{ color: 'black' }}
                                        _hover={{ bg: "teal.100", cursor: "pointer" }}
                                        transition="background-color 0.2s ease"
                                    >
                                        {user.full_name || user.email}
                                    </Text>
                                ))
                            ) : (
                                <Text color="gray.500" fontStyle="italic">
                                    Нет участников
                                </Text>
                            )}
                        </Box>
                    )}
                </Box>
            )}
            <VStack align="stretch">
                {messages.map((msg: ChatMsgResponse) => (
                    <Box 
                        key={msg.updated_at.toString()} 
                        p={2} 
                        borderWidth={1} 
                        borderRadius="md" 
                        mb={4} 
                        position="relative"
                        bg={Number(msg.sender_id) === Number(currentUserId) ? 'green.300' : 'yellow.300'}
                    >
                        <strong style={{ color: 'black' }}>{msg.sender.full_name || msg.sender.email}:</strong>
                        <p style={{ color: 'black' }}>{msg.content}</p>
                        <Text fontSize="sm" color="gray.500">
                            {moment(msg.updated_at).locale('ru').format('LL [в] HH:mm')}
                        </Text>

                        {msg.sender_id == currentUserId && (
                            <Box 
                            position="absolute" 
                            right={2} 
                            top={2}
                            onMouseEnter={() => msg.read_by_users.length > 0 && setHoveredMessageId(msg.updated_at.toString())}
                            onMouseLeave={() => setHoveredMessageId(null)}
                        >
                            {msg.read_by_users.length === users.length - 1 ? ( // - 1 bc exclude myself
                                <span style={{ cursor: 'pointer', color: 'green' }}>✔️✔️</span>
                            ) : msg.read_by_users.length > 0 ? (
                                <>
                                    <span style={{ cursor: 'pointer', color: 'orange' }}>✔️</span>
                                    {type === 'group' && hoveredMessageId === msg.updated_at.toString() && (
                                        <div style={{ position: 'relative' }}>
                                            <div style={{
                                                backgroundColor: '#f0f0f0',
                                                padding: '5px',
                                                borderRadius: '5px',
                                                position: 'absolute',
                                                right: 0,
                                                zIndex: 10,
                                            }}>
                                                Прочитали:
                                                {msg.read_by_users.map((reader: UserShort) => (
                                                    <div key={reader.id}>{reader.full_name || reader.email}</div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </>
                            ) : (
                                <span style={{ color: 'gray' }}>⚪️</span>
                            )}
                        </Box>
                        )}
                    </Box>
                ))}
            </VStack>

            <HStack mt={4}>
                <Textarea 
                    value={newMessageContent}
                    onChange={(e) => setNewMessageContent(e.target.value)}
                    placeholder="Введите ваше сообщение..."
                    size="sm"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                      }
                    }}
                />
                <Button onClick={handleSendMessage} colorScheme="teal" loading={isSending}>Отправить</Button>

                <Button onClick={handleRefreshChat} colorScheme="blue">Обновить чат</Button>
            </HStack>
        </Box>
    );
};

export default Chat;
