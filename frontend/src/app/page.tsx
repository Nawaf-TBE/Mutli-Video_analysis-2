'use client';

import React, { useState } from 'react';
import { Upload, Play, MessageCircle, Search, Video } from 'lucide-react';
import VideoUpload from '@/components/VideoUpload';
import VideoPlayer from '@/components/VideoPlayer';
import ChatInterface from '@/components/ChatInterface';
import VisualSearch from '@/components/VisualSearch';
import { useVideo } from '@/context/VideoContext';

type TabType = 'upload' | 'player' | 'chat' | 'search';

const tabs = [
  { id: 'upload', label: 'Upload', icon: Upload },
  { id: 'player', label: 'Player', icon: Play },
  { id: 'chat', label: 'Chat', icon: MessageCircle },
  { id: 'search', label: 'Visual Search', icon: Search },
];

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<TabType>('upload');
  const { state } = useVideo();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <Video className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-xl font-bold text-gray-800">Multi-Video Analysis</h1>
                <p className="text-sm text-gray-600">AI-powered video processing and chat</p>
              </div>
            </div>
            
            {state.currentVideo && (
              <div className="text-right">
                <p className="text-sm font-medium text-gray-800">{state.currentVideo.title}</p>
                <p className="text-xs text-gray-500">Video ID: {state.currentVideo.id}</p>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                const isDisabled = tab.id !== 'upload' && !state.currentVideo;
                
                return (
                  <button
                    key={tab.id}
                    onClick={() => !isDisabled && setActiveTab(tab.id as TabType)}
                    disabled={isDisabled}
                    className={`
                      flex items-center gap-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors
                      ${isActive
                        ? 'border-blue-500 text-blue-600'
                        : isDisabled
                        ? 'border-transparent text-gray-400 cursor-not-allowed'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }
                    `}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="tab-content">
          {activeTab === 'upload' && (
            <div className="space-y-6">
              <VideoUpload />
              
              {!state.currentVideo && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                  <h3 className="text-lg font-medium text-blue-800 mb-3">Welcome to Multi-Video Analysis!</h3>
                  <div className="space-y-2 text-blue-700">
                    <p>✨ Upload any YouTube video to get started</p>
                    <p>🤖 AI will automatically generate sections and transcripts</p>
                    <p>💬 Chat with the video content using RAG technology</p>
                    <p>🔍 Search for specific visual content in video frames</p>
                    <p>📊 Extract and analyze video frames with advanced embeddings</p>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {activeTab === 'player' && (
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
              <div className="xl:col-span-2">
                <VideoPlayer />
              </div>
              <div className="xl:col-span-1">
                <ChatInterface />
              </div>
            </div>
          )}
          
          {activeTab === 'chat' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <ChatInterface />
              </div>
              <div className="space-y-6">
                {state.currentVideo && (
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4">Video Information</h3>
                    <div className="space-y-2 text-sm">
                      <p><span className="font-medium">Title:</span> {state.currentVideo.title}</p>
                      <p><span className="font-medium">URL:</span> {state.currentVideo.url}</p>
                      <p><span className="font-medium">Sections:</span> {state.sections.length}</p>
                      <p><span className="font-medium">Frames:</span> {state.frames.length}</p>
                    </div>
                  </div>
                )}
                
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4">Chat Tips</h3>
                  <div className="space-y-2 text-sm text-gray-600">
                    <p>• Ask about specific topics or timestamps</p>
                    <p>• Request summaries of video sections</p>
                    <p>• Ask for explanations of complex concepts</p>
                    <p>• Get citations with timestamps for verification</p>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'search' && <VisualSearch />}
        </div>

        {/* Loading Overlay */}
        {state.isLoading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-8 max-w-sm w-full mx-4">
              <div className="text-center">
                <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-gray-800 font-medium">Processing video...</p>
                <p className="text-gray-600 text-sm mt-2">This may take a few minutes</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
