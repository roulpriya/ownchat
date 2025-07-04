import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Chat, Message } from '../types';
import { chatAPI, messageAPI } from '../services/api';
import Sidebar from './Sidebar';
import ChatWindow from './ChatWindow';

const ChatInterface: React.FC = () => {
  const { chatId } = useParams<{ chatId: string }>();
  const navigate = useNavigate();
  
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChat, setCurrentChat] = useState<Chat | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    loadChats();
  }, []);

  useEffect(() => {
    if (chatId) {
      loadChat(chatId);
    } else {
      setCurrentChat(null);
      setMessages([]);
    }
  }, [chatId]);

  const loadChats = async () => {
    try {
      const chatsData = await chatAPI.getChats();
      setChats(chatsData);
    } catch (error) {
      console.error('Failed to load chats:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadChat = async (id: string) => {
    try {
      const chat = await chatAPI.getChat(id);
      setCurrentChat(chat);
      setMessages(chat.messages || []);
    } catch (error) {
      console.error('Failed to load chat:', error);
      navigate('/chat');
    }
  };

  const createNewChat = async (title?: string, model?: string) => {
    try {
      const newChat = await chatAPI.createChat({ title, model: model || 'gpt-4' });
      setChats([newChat, ...chats]);
      navigate(`/chat/${newChat.id}`);
      return newChat;
    } catch (error) {
      console.error('Failed to create chat:', error);
      throw error;
    }
  };

  const deleteChat = async (id: string) => {
    try {
      await chatAPI.deleteChat(id);
      setChats(chats.filter(chat => chat.id !== id));
      if (currentChat?.id === id) {
        navigate('/chat');
      }
    } catch (error) {
      console.error('Failed to delete chat:', error);
      throw error;
    }
  };

  const updateChatTitle = async (id: string, title: string) => {
    try {
      const updatedChat = await chatAPI.updateChat(id, { title });
      setChats(chats.map(chat => chat.id === id ? updatedChat : chat));
      if (currentChat?.id === id) {
        setCurrentChat(updatedChat);
      }
    } catch (error) {
      console.error('Failed to update chat title:', error);
      throw error;
    }
  };

  const updateChat = async (id: string, updates: Partial<Chat>) => {
    try {
      const updatedChat = await chatAPI.updateChat(id, updates);
      setChats(chats.map(chat => chat.id === id ? updatedChat : chat));
      if (currentChat?.id === id) {
        setCurrentChat(updatedChat);
      }
    } catch (error) {
      console.error('Failed to update chat:', error);
      throw error;
    }
  };

  const sendMessage = async (content: string) => {
    if (!currentChat) {
      // Create a new chat if none exists
      const newChat = await createNewChat();
      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        content,
        role: 'user',
        timestamp: new Date().toISOString(),
        chat_id: newChat.id
      };
      setMessages([userMessage]);
      setSendingMessage(true);

      try {
        const response = await messageAPI.sendMessage(newChat.id, { content });
        // Update messages with both user and AI messages
        setMessages([response.user_message, response.ai_message]);
        
        // Update the chat list with the updated chat
        loadChats();
      } catch (error) {
        console.error('Failed to send message:', error);
        setMessages([]);
      } finally {
        setSendingMessage(false);
      }
    } else {
      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        content,
        role: 'user',
        timestamp: new Date().toISOString(),
        chat_id: currentChat.id
      };
      setMessages(prev => [...prev, userMessage]);
      setSendingMessage(true);

      try {
        const response = await messageAPI.sendMessage(currentChat.id, { content });
        // Replace temp user message and add AI response
        setMessages(prev => [...prev.filter(msg => msg.id !== userMessage.id), response.user_message, response.ai_message]);
        
        // Update the chat list with the updated chat
        loadChats();
      } catch (error) {
        console.error('Failed to send message:', error);
        setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
      } finally {
        setSendingMessage(false);
      }
    }
  };

  const searchChats = async (query: string) => {
    try {
      return await chatAPI.searchChats(query);
    } catch (error) {
      console.error('Failed to search chats:', error);
      return [];
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar
        chats={chats}
        currentChatId={currentChat?.id}
        onCreateChat={createNewChat}
        onDeleteChat={deleteChat}
        onUpdateChatTitle={updateChatTitle}
        onSearchChats={searchChats}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      
      <div className="flex-1 flex flex-col">
        <ChatWindow
          chat={currentChat}
          messages={messages}
          onSendMessage={sendMessage}
          onUpdateChat={updateChat}
          loading={sendingMessage}
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        />
      </div>
    </div>
  );
};

export default ChatInterface;