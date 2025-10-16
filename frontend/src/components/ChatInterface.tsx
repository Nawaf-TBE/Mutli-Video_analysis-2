'use client';

import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
import { Send, MessageCircle, Bot, User, Clock, Trash2 } from 'lucide-react';
import { useVideo } from '@/context/VideoContext';
import { chatWithVideo } from '@/lib/api';

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  citations?: Array<{
    timestamp: number;
    content: string;
  }>;
}

type Citation = NonNullable<Message['citations']>[number];

const MessageBubble = memo(function MessageBubble({
  msg,
  formatTime,
}: {
  msg: Message;
  formatTime: (seconds: number) => string;
}) {
  return (
    <div
      className={`flex gap-3 ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
      role="listitem"
      aria-live={msg.type === 'bot' ? 'polite' : undefined}
    >
      {msg.type === 'bot' && (
        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
          <Bot className="w-4 h-4 text-blue-600" />
        </div>
      )}
      
      <div className={`max-w-[70%] ${msg.type === 'user' ? 'order-1' : ''}`}>
        <div
          className={`p-3 rounded-lg ${
            msg.type === 'user'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-800'
          }`}
        >
          <p className="whitespace-pre-wrap">{msg.content}</p>
        </div>
        
        {msg.citations && msg.citations.length > 0 && (
          <div className="mt-2 space-y-1">
            {msg.citations.map((citation: Citation, index: number) => (
              <div
                key={index}
                className="text-xs bg-blue-50 border border-blue-200 rounded p-2 flex items-center gap-2"
              >
                <Clock className="w-3 h-3 text-blue-600" />
                <span className="font-medium text-blue-700">{formatTime(citation.timestamp)}</span>
                <span className="text-gray-600">-</span>
                <span className="text-gray-700">{citation.content}</span>
              </div>
            ))}
          </div>
        )}
        
        <div className="text-xs text-gray-500 mt-1">{msg.timestamp.toLocaleTimeString()}</div>
      </div>

      {msg.type === 'user' && (
        <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0">
          <User className="w-4 h-4 text-gray-600" />
        </div>
      )}
    </div>
  );
});

export default function ChatInterface() {
  const { state, addChatMessage, clearChat } = useVideo();
  const { currentVideo, chatHistory, conversationId } = state;
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [localMessages, setLocalMessages] = useState<Message[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const messages: Message[] = chatHistory.map((chat, index) => ({
      id: `bot-${index}`,
      type: 'bot',
      content: chat.response,
      timestamp: new Date(),
      citations: chat.citations,
    }));
    setLocalMessages(messages);
  }, [chatHistory]);

  useEffect(() => {
    scrollToBottom();
  }, [localMessages]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || !currentVideo || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: message.trim(),
      timestamp: new Date(),
    };

    setLocalMessages(prev => [...prev, userMessage]);
    setMessage('');
    setIsLoading(true);

    try {
      const activeVideoId = currentVideo.id;
      const activeConversationId = conversationId || undefined;

      const response = await chatWithVideo(
        activeVideoId,
        userMessage.content,
        activeConversationId
      );

      const botMessage: Message = {
        id: `bot-${Date.now()}`,
        type: 'bot',
        content: response.response,
        timestamp: new Date(),
        citations: response.citations,
      };

      setLocalMessages(prev => [...prev, botMessage]);
      addChatMessage(response);
    } catch (error: unknown) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        type: 'bot',
        content: `Sorry, I encountered an error: ${
          error instanceof Error 
            ? error.message 
            : 'Failed to get response'
        }`,
        timestamp: new Date(),
      };
      setLocalMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    setLocalMessages([]);
    clearChat();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!currentVideo) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="text-gray-400 mb-4">
          <MessageCircle className="w-16 h-16 mx-auto" />
        </div>
        <h3 className="text-lg font-medium text-gray-600 mb-2">No Video Selected</h3>
        <p className="text-gray-500">Upload a video to start chatting about its content</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md h-[600px] flex flex-col">
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageCircle className="w-5 h-5 text-blue-600" />
          <h4 className="font-medium text-gray-800">Chat with Video</h4>
        </div>
        {localMessages.length > 0 && (
          <button
            onClick={handleClearChat}
            className="flex items-center gap-1 px-2 py-1 text-sm text-red-600 hover:bg-red-50 rounded-md"
            aria-label="Clear chat"
          >
            <Trash2 className="w-4 h-4" />
            Clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4" role="list" aria-label="Messages">
        {localMessages.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Bot className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="mb-2">Start a conversation about the video!</p>
            <p className="text-sm">
              Ask questions about the content, request summaries, or explore specific topics.
            </p>
          </div>
        ) : (
          localMessages.map((msg) => (
            <MessageBubble key={msg.id} msg={msg} formatTime={formatTime} />
          ))
        )}
        
        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 text-blue-600" />
            </div>
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t">
        <form onSubmit={handleSubmit} className="flex gap-2" aria-label="Chat input">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask about the video content..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
            disabled={isLoading || !currentVideo}
            aria-disabled={isLoading || !currentVideo}
            aria-label="Message"
          />
          <button
            type="submit"
            disabled={!message.trim() || isLoading || !currentVideo}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Send message"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
} 