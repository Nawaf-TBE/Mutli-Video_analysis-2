'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Search, Image, Clock, Grid } from 'lucide-react';
import { useVideo } from '@/context/VideoContext';
import { visualSearch, getFrames, extractFrames, generateEmbeddings, VisualSearchResult } from '@/lib/api';

export default function VisualSearch() {
  const { state, setFrames } = useVideo();
  const { currentVideo, frames } = state;
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<VisualSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchType, setSearchType] = useState<'text' | 'visual' | 'hybrid'>('hybrid');
  const [isExtractingFrames, setIsExtractingFrames] = useState(false);
  const [isGeneratingEmbeddings, setIsGeneratingEmbeddings] = useState(false);

  const loadFrames = useCallback(async () => {
    if (!currentVideo) return;
    
    try {
      const videoFrames = await getFrames(currentVideo.id);
      setFrames(videoFrames);
    } catch (error) {
      console.error('Failed to load frames:', error);
    }
  }, [currentVideo, setFrames]);

  useEffect(() => {
    if (currentVideo) {
      loadFrames();
    }
  }, [currentVideo, loadFrames]);

  const handleExtractFrames = async () => {
    if (!currentVideo) return;
    
    setIsExtractingFrames(true);
    try {
      await extractFrames(currentVideo.id, 10); // Extract every 10 seconds
      await loadFrames(); // Reload frames
    } catch (error) {
      console.error('Failed to extract frames:', error);
    } finally {
      setIsExtractingFrames(false);
    }
  };

  const handleGenerateEmbeddings = async () => {
    if (!currentVideo) return;
    
    setIsGeneratingEmbeddings(true);
    try {
      await generateEmbeddings(currentVideo.id, true, true);
    } catch (error) {
      console.error('Failed to generate embeddings:', error);
    } finally {
      setIsGeneratingEmbeddings(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !currentVideo || isSearching) return;

    setIsSearching(true);
    try {
      const response = await visualSearch(currentVideo.id, query.trim(), searchType, 20);
      setSearchResults(response.results || []);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  if (!currentVideo) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="text-gray-400 mb-4">
          <Search className="w-16 h-16 mx-auto" />
        </div>
        <h3 className="text-lg font-medium text-gray-600 mb-2">No Video Selected</h3>
        <p className="text-gray-500">Upload a video to start visual search</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Setup Panel */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center gap-3 mb-4">
          <Grid className="w-5 h-5 text-purple-600" />
          <h4 className="font-medium text-gray-800">Video Processing</h4>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <h5 className="font-medium text-gray-700 mb-2">Frames</h5>
            <p className="text-2xl font-bold text-blue-600 mb-2">{frames.length}</p>
            <button
              onClick={handleExtractFrames}
              disabled={isExtractingFrames}
              className="w-full px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 text-sm"
            >
              {isExtractingFrames ? 'Extracting...' : 'Extract Frames'}
            </button>
          </div>

          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <h5 className="font-medium text-gray-700 mb-2">Embeddings</h5>
            <p className="text-2xl font-bold text-purple-600 mb-2">
              {frames.length > 0 ? 'Ready' : 'None'}
            </p>
            <button
              onClick={handleGenerateEmbeddings}
              disabled={isGeneratingEmbeddings || frames.length === 0}
              className="w-full px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 text-sm"
            >
              {isGeneratingEmbeddings ? 'Generating...' : 'Generate'}
            </button>
          </div>

          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <h5 className="font-medium text-gray-700 mb-2">Search Results</h5>
            <p className="text-2xl font-bold text-green-600 mb-2">{searchResults.length}</p>
            <div className="text-sm text-gray-500">Last search</div>
          </div>
        </div>
      </div>

      {/* Search Panel */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center gap-3 mb-6">
          <Search className="w-5 h-5 text-blue-600" />
          <h4 className="font-medium text-gray-800">Visual Search</h4>
        </div>

        <form onSubmit={handleSearch} className="space-y-4">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
              Search Query
            </label>
            <input
              type="text"
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe what you're looking for in the video..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isSearching}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Type
            </label>
            <div className="flex gap-2">
              {[
                { value: 'text', label: 'Text Only', icon: '📝' },
                { value: 'visual', label: 'Visual Only', icon: '👁️' },
                { value: 'hybrid', label: 'Hybrid', icon: '🔄' },
              ].map((type) => (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => setSearchType(type.value as 'text' | 'visual' | 'hybrid')}
                  className={`flex-1 px-3 py-2 rounded-lg border text-sm font-medium ${
                    searchType === type.value
                      ? 'bg-blue-50 border-blue-300 text-blue-700'
                      : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {type.icon} {type.label}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={!query.trim() || isSearching || frames.length === 0}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isSearching ? (
              <>
                <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
                Searching...
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                Search Frames
              </>
            )}
          </button>
        </form>

        {frames.length === 0 && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700 text-sm">
            No frames available. Extract frames first to enable search.
          </div>
        )}
      </div>

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Image className="w-5 h-5 text-green-600" />
              <h4 className="font-medium text-gray-800">Search Results</h4>
              <span className="text-sm text-gray-500">({searchResults.length} frames)</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {searchResults.map((result, index) => (
              <div key={`${result.frame_id}-${index}`} className="border border-gray-200 rounded-lg overflow-hidden">
                {/* Frame Image Placeholder */}
                <div className="aspect-video bg-gray-100 flex items-center justify-center">
                  <div className="text-center text-gray-500">
                    <Image className="w-8 h-8 mx-auto mb-2" aria-label={`Frame ${result.frame_id}`} />
                    <p className="text-sm">Frame {result.frame_id}</p>
                  </div>
                </div>

                {/* Frame Info */}
                <div className="p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="flex items-center gap-1 text-sm text-gray-600">
                      <Clock className="w-4 h-4" />
                      {formatTime(result.timestamp)}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getScoreColor(result.score)}`}>
                      {(result.score * 100).toFixed(1)}%
                    </span>
                  </div>
                  
                  <div className="text-xs text-gray-500">
                    Match: {result.match_type}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {searchResults.length === 0 && query && !isSearching && (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <div className="text-gray-400 mb-4">
            <Search className="w-12 h-12 mx-auto" aria-label="No search results icon" />
          </div>
          <h3 className="text-lg font-medium text-gray-600 mb-2">No Results Found</h3>
          <p className="text-gray-500">Try a different search query or search type</p>
        </div>
      )}
    </div>
  );
} 