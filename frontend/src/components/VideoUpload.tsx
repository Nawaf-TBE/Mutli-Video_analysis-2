'use client';

import React, { useState } from 'react';
import { Upload, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadVideo } from '@/lib/api';
import { useVideo } from '@/context/VideoContext';

export default function VideoUpload() {
  const [url, setUrl] = useState('');
  const [uploading, setUploading] = useState(false);
  const { setVideo, setLoading, setError, state } = useVideo();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setUploading(true);
    setLoading(true);
    setError(null);

    try {
      const video = await uploadVideo(url.trim());
      setVideo(video);
      setUrl('');
    } catch (error: unknown) {
      const isAxiosError = error && typeof error === 'object' && 'response' in error;
      const errorMessage = isAxiosError 
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Failed to upload video'
        : 'Failed to upload video';
      setError(errorMessage);
    } finally {
      setUploading(false);
      setLoading(false);
    }
  };

  const isValidYouTubeUrl = (url: string) => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\//;
    return youtubeRegex.test(url);
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center gap-3 mb-6">
          <Upload className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-800">Upload YouTube Video</h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
              YouTube URL
            </label>
            <input
              type="url"
              id="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={uploading}
            />
            {url && !isValidYouTubeUrl(url) && (
              <p className="text-red-500 text-sm mt-1">Please enter a valid YouTube URL</p>
            )}
          </div>

          <button
            type="submit"
            disabled={!url.trim() || !isValidYouTubeUrl(url) || uploading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {uploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Processing Video...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Upload & Process
              </>
            )}
          </button>
        </form>

        {state.error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <p className="text-red-700">{state.error}</p>
          </div>
        )}

        {state.currentVideo && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <div>
              <p className="text-green-700 font-medium">Video uploaded successfully!</p>
              <p className="text-green-600 text-sm">{state.currentVideo.title}</p>
            </div>
          </div>
        )}

        <div className="mt-6 text-sm text-gray-600">
          <h3 className="font-medium mb-2">What happens after upload:</h3>
          <ul className="space-y-1 list-disc list-inside">
            <li>Video metadata is extracted</li>
            <li>Transcript is fetched and processed</li>
            <li>AI-generated sections are created</li>
            <li>Video is ready for analysis and chat</li>
          </ul>
        </div>
      </div>
    </div>
  );
} 