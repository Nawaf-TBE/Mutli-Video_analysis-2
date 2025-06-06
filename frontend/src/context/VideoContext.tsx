'use client';

import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { Video, Section, Frame, ChatResponse } from '@/lib/api';

interface VideoState {
  currentVideo: Video | null;
  sections: Section[];
  frames: Frame[];
  chatHistory: ChatResponse[];
  isLoading: boolean;
  error: string | null;
  conversationId: string | null;
}

type VideoAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_VIDEO'; payload: Video }
  | { type: 'SET_SECTIONS'; payload: Section[] }
  | { type: 'SET_FRAMES'; payload: Frame[] }
  | { type: 'ADD_CHAT_MESSAGE'; payload: ChatResponse }
  | { type: 'CLEAR_CHAT' }
  | { type: 'SET_CONVERSATION_ID'; payload: string }
  | { type: 'RESET' };

const initialState: VideoState = {
  currentVideo: null,
  sections: [],
  frames: [],
  chatHistory: [],
  isLoading: false,
  error: null,
  conversationId: null,
};

function videoReducer(state: VideoState, action: VideoAction): VideoState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };
    case 'SET_VIDEO':
      return { ...state, currentVideo: action.payload, error: null };
    case 'SET_SECTIONS':
      return { ...state, sections: action.payload };
    case 'SET_FRAMES':
      return { ...state, frames: action.payload };
    case 'ADD_CHAT_MESSAGE':
      return { 
        ...state, 
        chatHistory: [...state.chatHistory, action.payload],
        conversationId: action.payload.conversation_id 
      };
    case 'CLEAR_CHAT':
      return { ...state, chatHistory: [], conversationId: null };
    case 'SET_CONVERSATION_ID':
      return { ...state, conversationId: action.payload };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

interface VideoContextType {
  state: VideoState;
  dispatch: React.Dispatch<VideoAction>;
  setVideo: (video: Video) => void;
  setSections: (sections: Section[]) => void;
  setFrames: (frames: Frame[]) => void;
  addChatMessage: (message: ChatResponse) => void;
  clearChat: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const VideoContext = createContext<VideoContextType | undefined>(undefined);

export function VideoProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(videoReducer, initialState);

  const contextValue: VideoContextType = {
    state,
    dispatch,
    setVideo: (video) => dispatch({ type: 'SET_VIDEO', payload: video }),
    setSections: (sections) => dispatch({ type: 'SET_SECTIONS', payload: sections }),
    setFrames: (frames) => dispatch({ type: 'SET_FRAMES', payload: frames }),
    addChatMessage: (message) => dispatch({ type: 'ADD_CHAT_MESSAGE', payload: message }),
    clearChat: () => dispatch({ type: 'CLEAR_CHAT' }),
    setLoading: (loading) => dispatch({ type: 'SET_LOADING', payload: loading }),
    setError: (error) => dispatch({ type: 'SET_ERROR', payload: error }),
    reset: () => dispatch({ type: 'RESET' }),
  };

  return (
    <VideoContext.Provider value={contextValue}>
      {children}
    </VideoContext.Provider>
  );
}

export function useVideo() {
  const context = useContext(VideoContext);
  if (context === undefined) {
    throw new Error('useVideo must be used within a VideoProvider');
  }
  return context;
} 