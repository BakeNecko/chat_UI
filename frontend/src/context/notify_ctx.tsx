import React, { useEffect } from 'react';
import { Box, Text, Button } from '@chakra-ui/react';
import { useWebSocket } from './ws_chat_ctx';

const Notification = ({ notification, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose(notification);
    }, 10000);

    return () => clearTimeout(timer);
  }, [notification, onClose]);

  return (
    <Box 
      p={4} 
      borderWidth={1} 
      borderRadius="md" 
      mb={2} 
      bg="teal.100" 
      boxShadow="md" 
      width="20vw"
      maxWidth="300px"
      minWidth="150px"
    >
      <Text style={{ color: 'black' }}>{notification.content}</Text>
      <Button mt={2} size="sm" onClick={() => onClose(notification)}>Скрыть</Button>
    </Box>
  );
};

const NotificationList = () => {
  const { notifications, setNotifications } = useWebSocket();

  const handleClose = (notificationToRemove) => {
    setNotifications((prevNotifications) =>
      prevNotifications.filter((notification) => notification !== notificationToRemove)
    );
  };

  return (
    <Box 
      position="fixed" 
      bottom="20px" 
      left="20px" 
      zIndex="1000"
      display="flex"
      flexDirection="column"
      alignItems="flex-start"
      width="22vw"
      maxWidth="320px"
      minWidth="160px"
    >
      {notifications.map((notification) => (
        <Notification key={notification.content} notification={notification} onClose={handleClose} />
      ))}
    </Box>
  );
};

export default NotificationList;