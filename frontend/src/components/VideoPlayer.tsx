'use client';

import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
import ReactPlayer from 'react-player';
import { Play, RotateCcw, Clock, List } from 'lucide-react';
import { useVideo } from '@/context/VideoContext';
import { getVideoSections, regenerateSections } from '@/lib/api';

interface Section {
  id: number;
  title: string;
  start_time: number;
  end_time: number;
}

interface VideoInfoProps {
  title: string;
  currentTime: number;
  duration: number;
  currentSection: Section | null;
  formatTime: (seconds: number) => string;
}

interface SectionItemProps {
  section: Section;
  isActive: boolean;
  onSeek: (time: number) => void;
  formatTime: (seconds: number) => string;
}

const VideoInfo = memo(function VideoInfo({
  title,
  currentTime,
  duration,
  currentSection,
  formatTime,
}: VideoInfoProps) {
  return (
    <div className="p-4 border-b">
      <h3 className="text-lg font-semibold text-gray-800 mb-2">{title}</h3>
      <div className="flex items-center gap-4 text-sm text-gray-600">
        <span className="flex items-center gap-1">
          <Clock className="w-4 h-4" />
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>
        {currentSection && (
          <span className="text-blue-600 font-medium">
            Current: {currentSection.title}
          </span>
        )}
      </div>
    </div>
  );
});

const SectionItem = memo(function SectionItem({
  section,
  isActive,
  onSeek,
  formatTime,
}: SectionItemProps) {
  const handleClick = useCallback(() => {
    onSeek(section.start_time);
  }, [onSeek, section.start_time]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }, [handleClick]);

  return (
    <div
      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
        isActive 
          ? 'bg-blue-50 border-blue-200' 
          : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
      }`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-label={`Go to section: ${section.title} at ${formatTime(section.start_time)}`}
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
});

// Custom hook for video sections management
function useVideoSections(currentVideo: any) {
  const { setSections } = useVideo();
  const [loadingSections, setLoadingSections] = useState(false);

  const loadSections = useCallback(async () => {
    if (!currentVideo) return;
    
    setLoadingSections(true);
    try {
      const videoSections = await getVideoSections(currentVideo.id);
      setSections(Array.isArray(videoSections) ? videoSections : []);
    } catch (error) {
      console.error('Failed to load sections:', error);
    } finally {
      setLoadingSections(false);
    }
  }, [currentVideo, setSections]);

  const handleRegenerateSections = useCallback(async () => {
    if (!currentVideo) return;
    
    setLoadingSections(true);
    try {
      const newSections = await regenerateSections(currentVideo.id);
      setSections(Array.isArray(newSections) ? newSections : []);
    } catch (error) {
      console.error('Failed to regenerate sections:', error);
    } finally {
      setLoadingSections(false);
    }
  }, [currentVideo, setSections]);

  return { loadSections, regenerateSections, loadingSections };
}

// Custom hook for player state management
function usePlayerState() {
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const playerRef = useRef<ReactPlayer>(null);

  const seekToTime = useCallback((time: number) => {
    if (playerRef.current) {
      playerRef.current.seekTo(time);
      setCurrentTime(time);
    }
  }, []);

  const handlePlay = useCallback(() => setPlaying(true), []);
  const handlePause = useCallback(() => setPlaying(false), []);
  const handleProgress = useCallback(({ playedSeconds }: { playedSeconds: number }) => {
    setCurrentTime(playedSeconds);
  }, []);
  const handleDuration = useCallback((duration: number) => {
    setDuration(duration);
  }, []);

  return {
    playing,
    currentTime,
    duration,
    playerRef,
    seekToTime,
    handlePlay,
    handlePause,
    handleProgress,
    handleDuration,
  };
}

export default function VideoPlayer() {
  const { state } = useVideo();
  const { currentVideo, sections } = state;
  const { loadSections, handleRegenerateSections, loadingSections } = useVideoSections(currentVideo);
  const {
    playing,
    currentTime,
    duration,
    playerRef,
    seekToTime,
    handlePlay,
    handlePause,
    handleProgress,
    handleDuration,
  } = usePlayerState();

  useEffect(() => {
    if (currentVideo && (!sections || sections.length === 0)) {
      loadSections();
    }
  }, [currentVideo?.id, sections?.length, loadSections]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getCurrentSection = useCallback(() => {
    if (!sections || !Array.isArray(sections)) return null;
    return sections.find(section => 
      currentTime >= section.start_time && currentTime <= section.end_time
    ) || null;
  }, [sections, currentTime]);

  const currentSection = getCurrentSection();

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
            onPlay={handlePlay}
            onPause={handlePause}
            onProgress={handleProgress}
            onDuration={handleDuration}
            config={{
              youtube: {
                playerVars: {
                  origin: window.location.origin,
                  modestbranding: 1,
                  rel: 0,
                  showinfo: 0
                }
              }
            }}
          />
        </div>
        
        {/* Video Info */}
        <VideoInfo
          title={currentVideo.title}
          currentTime={currentTime}
          duration={duration}
          currentSection={currentSection}
          formatTime={formatTime}
        />
      </div>

      {/* Sections Panel */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-4 border-b flex items-center justify-between">
          <div className="flex items-center gap-2">
            <List className="w-5 h-5 text-gray-600" />
            <h4 className="font-medium text-gray-800">Video Sections</h4>
            {sections && sections.length > 0 && (
              <span className="text-sm text-gray-500">({sections.length})</span>
            )}
          </div>
          <button
            onClick={handleRegenerateSections}
            disabled={loadingSections}
            className="flex items-center gap-2 px-3 py-1 text-sm bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 disabled:opacity-50"
            aria-label="Regenerate video sections"
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
          ) : sections && sections.length > 0 ? (
            <div className="space-y-2" role="list" aria-label="Video sections">
              {sections.map((section) => {
                const isActive = currentTime >= section.start_time && currentTime <= section.end_time;
                
                return (
                  <SectionItem
                    key={section.id}
                    section={section}
                    isActive={isActive}
                    onSeek={seekToTime}
                    formatTime={formatTime}
                  />
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