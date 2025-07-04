import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Chat } from '../types';
import {
  PlusIcon,
  XMarkIcon,
  TrashIcon,
  PencilIcon,
  UserIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline';

interface SidebarProps {
  chats: Chat[];
  currentChatId?: string;
  onCreateChat: (title?: string) => Promise<Chat>;
  onDeleteChat: (id: string) => Promise<void>;
  onUpdateChatTitle: (id: string, title: string) => Promise<void>;
  isOpen: boolean;
  onToggle: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  chats,
  currentChatId,
  onCreateChat,
  onDeleteChat,
  onUpdateChatTitle,
  isOpen,
  onToggle,
}) => {
  const { user, logout } = useAuth();
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const handleCreateNewChat = async () => {
    try {
      await onCreateChat();
    } catch (error) {
      console.error('Failed to create new chat:', error);
    }
  };

  const handleDeleteChat = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this chat?')) {
      try {
        await onDeleteChat(id);
      } catch (error) {
        console.error('Failed to delete chat:', error);
      }
    }
  };

  const handleEditChat = (chat: Chat, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setEditingChatId(chat.id);
    setEditTitle(chat.title);
  };

  const handleSaveEdit = async () => {
    if (editingChatId && editTitle.trim()) {
      try {
        await onUpdateChatTitle(editingChatId, editTitle.trim());
        setEditingChatId(null);
        setEditTitle('');
      } catch (error) {
        console.error('Failed to update chat title:', error);
      }
    }
  };

  const handleCancelEdit = () => {
    setEditingChatId(null);
    setEditTitle('');
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const groupChatsByDate = (chats: Chat[]) => {
    const groups: { [key: string]: Chat[] } = {};
    
    chats.forEach(chat => {
      const dateKey = formatDate(chat.created_at);
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(chat);
    });

    return groups;
  };

  const chatGroups = groupChatsByDate(chats);

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed lg:relative inset-y-0 left-0 z-50 w-80 bg-gray-900 transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        ${!isOpen ? 'lg:w-0 lg:overflow-hidden' : ''}
      `}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-700">
            <h2 className="text-lg font-semibold text-white">OwnChat</h2>
            <button
              onClick={onToggle}
              className="p-2 text-gray-400 hover:text-white lg:hidden"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>

          {/* New Chat Button */}
          <div className="p-4">
            <button
              onClick={handleCreateNewChat}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
            >
              <PlusIcon className="h-4 w-4" />
              New Chat
            </button>
          </div>

          {/* Chat List */}
          <div className="flex-1 overflow-y-auto px-2">
            {Object.entries(chatGroups).map(([dateGroup, groupChats]) => (
              <div key={dateGroup} className="mb-6">
                <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider px-3 mb-2">
                  {dateGroup}
                </h3>
                <div className="space-y-1">
                  {groupChats.map((chat) => (
                    <div key={chat.id} className="group relative">
                      {editingChatId === chat.id ? (
                        <div className="px-3 py-2">
                          <input
                            type="text"
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleSaveEdit();
                              if (e.key === 'Escape') handleCancelEdit();
                            }}
                            onBlur={handleSaveEdit}
                            className="w-full bg-gray-800 text-white text-sm rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            autoFocus
                          />
                        </div>
                      ) : (
                        <Link
                          to={`/chat/${chat.id}`}
                          className={`
                            block px-3 py-2 rounded-lg text-sm transition-colors group-hover:bg-gray-800
                            ${currentChatId === chat.id 
                              ? 'bg-gray-800 text-white' 
                              : 'text-gray-300 hover:text-white'
                            }
                          `}
                        >
                          <div className="flex items-center justify-between">
                            <span className="truncate flex-1 mr-2">
                              {chat.title || 'New Chat'}
                            </span>
                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={(e) => handleEditChat(chat, e)}
                                className="p-1 text-gray-400 hover:text-white"
                              >
                                <PencilIcon className="h-3 w-3" />
                              </button>
                              <button
                                onClick={(e) => handleDeleteChat(chat.id, e)}
                                className="p-1 text-gray-400 hover:text-red-400"
                              >
                                <TrashIcon className="h-3 w-3" />
                              </button>
                            </div>
                          </div>
                        </Link>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* User Section */}
          <div className="border-t border-gray-700 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
                  <UserIcon className="h-5 w-5 text-gray-300" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">
                    {user?.name || user?.email}
                  </p>
                  <p className="text-xs text-gray-400 truncate">
                    {user?.email}
                  </p>
                </div>
              </div>
              <button
                onClick={logout}
                className="p-2 text-gray-400 hover:text-white transition-colors"
                title="Sign out"
              >
                <ArrowRightOnRectangleIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;