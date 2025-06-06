'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import ReactPlayer from 'react-player';
import { Play, RotateCcw, Clock, List } from 'lucide-react';
import { useVideo } from '@/context/VideoContext';
import { getVideoSections, regenerateSections } from '@/lib/api';

export default function VideoPlayer() {
  const { state, setSections } = useVideo();
  const { currentVideo, sections } = state;
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [loadingSections, setLoadingSections] = useState(false);
  const playerRef = useRef<ReactPlayer>(null);

  const loadSections = useCallback(async () => {
    if (!currentVideo) return;
    
    setLoadingSections(true);
    try {
      const videoSections = await getVideoSections(currentVideo.id);
      setSections(videoSections);
    } catch (error) {
      console.error('Failed to load sections:', error);
    } finally {
      setLoadingSections(false);
    }
  }, [currentVideo, setSections]);

  useEffect(() => {
    if (currentVideo) {
      loadSections();
    }
  }, [currentVideo, loadSections]);

  const handleRegenerateSections = async () => {
    if (!currentVideo) return;
    
    setLoadingSections(true);
    try {
      const newSections = await regenerateSections(currentVideo.id);
      setSections(newSections);
    } catch (error) {
      console.error('Failed to regenerate sections:', error);
    } finally {
      setLoadingSections(false);
    }
  };

  const seekToTime = (time: number) => {
    if (playerRef.current) {
      playerRef.current.seekTo(time);
      setCurrentTime(time);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getCurrentSection = () => {
    return sections.find(section => 
      currentTime >= section.start_time && currentTime <= section.end_time
    );
  };

  if (!currentVideo) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="text-gray-400 mb-4">
          <Play className="w-16 h-16 mx-auto" />
        </div>
        <h3 className="text-lg font-medium text-gray-600 mb-2">No Video Selected</h3>
        <p className="text-gray-500">Upload a YouTube video to start watching and analyzing</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Video Player */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="aspect-video bg-black">
          <ReactPlayer
            ref={playerRef}
            url={currentVideo.url}
            width="100%"
            height="100%"
            playing={playing}
            controls={true}
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
            onProgress={({ playedSeconds }) => setCurrentTime(playedSeconds)}
            onDuration={setDuration}
          />
        </div>
        
        {/* Video Info */}
        <div className="p-4 border-b">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">{currentVideo.title}</h3>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>
            {getCurrentSection() && (
              <span className="text-blue-600 font-medium">
                Current: {getCurrentSection()?.title}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Sections Panel */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-4 border-b flex items-center justify-between">
          <div className="flex items-center gap-2">
            <List className="w-5 h-5 text-gray-600" />
            <h4 className="font-medium text-gray-800">Video Sections</h4>
            {sections.length > 0 && (
              <span className="text-sm text-gray-500">({sections.length})</span>
            )}
          </div>
          <button
            onClick={handleRegenerateSections}
            disabled={loadingSections}
            className="flex items-center gap-2 px-3 py-1 text-sm bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 disabled:opacity-50"
          >
            <RotateCcw className={`w-4 h-4 ${loadingSections ? 'animate-spin' : ''}`} />
            Regenerate
          </button>
        </div>

        <div className="p-4">
          {loadingSections ? (
            <div className="text-center py-8">
              <div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-2"></div>
              <p className="text-gray-600">Loading sections...</p>
            </div>
          ) : sections.length > 0 ? (
            <div className="space-y-2">
              {sections.map((section) => {
                const isActive = currentTime >= section.start_time && currentTime <= section.end_time;
                
                return (
                  <div
                    key={section.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      isActive 
                        ? 'bg-blue-50 border-blue-200' 
                        : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                    }`}
                    onClick={() => seekToTime(section.start_time)}
                  >
                    <div className="flex items-center justify-between">
                      <h5 className={`font-medium ${isActive ? 'text-blue-800' : 'text-gray-800'}`}>
                        {section.title}
                      </h5>
                      <span className="text-sm text-gray-500">
                        {formatTime(section.start_time)} - {formatTime(section.end_time)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <List className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No sections available</p>
              <p className="text-sm">Try regenerating sections or check if the video was processed correctly</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 