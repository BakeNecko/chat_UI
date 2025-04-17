import React, { useState } from 'react';
import { 
    Box,
    Heading, 
    Button,
    Input,
    Text,
    Stack,
} from '@chakra-ui/react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { ApiError, ChatService, CreateChatData, UserShort, UsersService } from '@/client';
import { Checkbox } from '../ui/checkbox';

interface CreateChatProps {
    onClose: () => void;
    onSuccess: () => void;
}
  
const CreateChat: React.FC<CreateChatProps> = ({ onClose, onSuccess }) => {
    const [chatName, setChatName] = useState('');
    const [selectedUsers, setSelectedUsers] = useState<number[]>([]);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const currentUserId = Number(localStorage.getItem("userId"));

    const { data: usersList = [], isLoading, isError } = useQuery<UserShort[], Error>({
        queryKey: ['usersList'],
        queryFn: async () => {
            const response = await UsersService.readUsers();
            return response.data.filter(user => Number(user.id) !== Number(currentUserId));
        }
    });
    const createChat = async (data: CreateChatData) => {
        await ChatService.createChat(data);
    };

    const mutation = useMutation({
        mutationFn: createChat,
        onSuccess: () => {
            console.log('Чат успешно создан');
            onSuccess(); 
            onClose();
            setChatName('');
            setSelectedUsers([]);
            setErrorMessage(null);
        },
        onError: (error: ApiError) => {
            console.error('Ошибка при создании чата:', error);
            if (typeof error.body === 'object' && error.body !== null) {
                // Извлечение сообщения об ошибке из error.body
                const body = error.body as { detail?: string }; 
                const errorMessage = body.detail || 'Неизвестная ошибка';
                setErrorMessage(`Не удалось создать чат. Пожалуйста, попробуйте еще раз. Ошибка: ${errorMessage}`);
            } else {
                setErrorMessage('Не удалось создать чат. Пожалуйста, попробуйте еще раз.');
        }
}});

    const toggleUserSelection = (id: number) => {
        setSelectedUsers((prev) =>
            prev.includes(id) ? prev.filter((uid) => uid !== id) : [...prev, id]
        );
    };

    const handleSubmit = () => {
        const data: CreateChatData = {
            name: chatName,
            user_ids: selectedUsers,
        };
        mutation.mutate(data);
    };

    if (isLoading) {
        return <Box>Загрузка пользователей...</Box>;
    }

    if (isError) {
        return <Box>Ошибка при загрузке пользователей.</Box>;
    }

    return (
        <Box
            bg="white"
            borderRadius="md"
            p={6}
            minWidth="320px"
            maxWidth="90vw"
            boxShadow="lg"
            position="relative"
        >
            <Heading size="md" mb={4}>
                Создать чат
            </Heading>

            <Input
                placeholder="Название чата"
                value={chatName}
                onChange={(e) => setChatName(e.target.value)}
                mb={4}
                style={{ color: 'black' }}
            />
            
            <Text style={{ color: 'black' }} mb={2}>Выберите пользователей:</Text>
            <Stack separator={<Box height="1" bg="gray.200" />} mb={4}>
                {usersList.map((user) => (
                    <Checkbox
                        key={user.id}
                        checked={selectedUsers.includes(Number(user.id))}
                        onChange={() => toggleUserSelection(Number(user.id))}
                    >
                        <Text style={{ color: 'black' }}>{user.full_name || user.email}</Text>
                    </Checkbox>
                ))}
            </Stack>

            {errorMessage && (
                <Text color="red.500" mb={4}>
                    {errorMessage}
                </Text>
            )}

            <Box display="flex" justifyContent="flex-end" gap={2}>
                <Button variant="outline" onClick={onClose}>
                    Отмена
                </Button>
                <Button colorScheme="blue" onClick={handleSubmit} disabled={!chatName || selectedUsers.length === 0}>
                    Создать
                </Button>
            </Box>
        </Box>
    );
};

export default CreateChat;
