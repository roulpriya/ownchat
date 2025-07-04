import axios, { AxiosResponse } from 'axios';
import Cookies from 'js-cookie';
import {
  User,
  Chat,
  Message,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  CreateChatRequest,
  SendMessageRequest,
  ChatSearchResult
} from '../types';

// Use relative URLs when in development (proxy will handle routing)
// Use full URL in production
const API_BASE_URL = import.meta.env.PROD
  ? (import.meta.env.VITE_API_URL || 'http://localhost:8000')
  : '';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Session-based authentication - no token storage needed
// Cookies are automatically handled by the browser

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Session expired or user not authenticated
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const response: AxiosResponse<AuthResponse> = await api.post('/api/auth/login', credentials);
    return response.data;
  },

  register: async (userData: RegisterRequest): Promise<AuthResponse> => {
    const response: AxiosResponse<AuthResponse> = await api.post('/api/auth/register', userData);
    return response.data;
  },

  googleLogin: async (credential: string): Promise<AuthResponse> => {
    const response: AxiosResponse<AuthResponse> = await api.post('/api/auth/google-login', {
      credential
    });

    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/api/auth/logout');
  },
};

// Chat API
export const chatAPI = {
  getChats: async (): Promise<Chat[]> => {
    const response: AxiosResponse<Chat[]> = await api.get('/api/chats');
    return response.data;
  },

  createChat: async (chatData: CreateChatRequest): Promise<Chat> => {
    const response: AxiosResponse<Chat> = await api.post('/api/chats', chatData);
    return response.data;
  },

  getChat: async (chatId: string): Promise<Chat> => {
    const response: AxiosResponse<Chat> = await api.get(`/api/chats/${chatId}`);
    return response.data;
  },

  updateChat: async (chatId: string, chatData: Partial<Chat>): Promise<Chat> => {
    const response: AxiosResponse<Chat> = await api.put(`/api/chats/${chatId}`, chatData);
    return response.data;
  },

  deleteChat: async (chatId: string): Promise<void> => {
    await api.delete(`/api/chats/${chatId}`);
  },

  searchChats: async (query: string): Promise<ChatSearchResult[]> => {
    const response: AxiosResponse<ChatSearchResult[]> = await api.get('/api/chats/search', {
      params: { q: query }
    });
    return response.data;
  },
};

// Message API
export const messageAPI = {
  sendMessage: async (chatId: string, messageData: SendMessageRequest): Promise<Message> => {
    const response: AxiosResponse<Message> = await api.post(`/api/chats/${chatId}/messages`, messageData);
    return response.data;
  },

  getMessages: async (chatId: string): Promise<Message[]> => {
    const response: AxiosResponse<Message[]> = await api.get(`/api/chats/${chatId}/messages`);
    return response.data;
  },
};

export default api;
