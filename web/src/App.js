import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Play, Square, Pause, Download, Upload, Search, Filter, AlertCircle } from 'lucide-react';

const KnowledgeHarvestApp = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [recordings, setRecordings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentView, setCurrentView] = useState('browse');
  const [recordingTime, setRecordingTime] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTags, setSelectedTags] = useState([]);
  const [showMetadataForm, setShowMetadataForm] = useState(false);
  const [metadata, setMetadata] = useState({ title: '', description: '', tags: '' });
  const [uploading, setUploading] = useState(false);

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);
  const chunksRef = useRef([]);

  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:3001';

  useEffect(() => {
    fetchRecordings();
  }, []);

  const fetchRecordings = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/recordings`);
      if (!response.ok) throw new Error('Failed to fetch recordings');
      const data = await response.json();
      setRecordings(data);
    } catch (err) {
      setError('Failed to load recordings: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      streamRef.current?.getTracks().forEach(track => track.stop());
      clearInterval(intervalRef.current);
      setIsRecording(false);
      setIsPaused(false);
    }
  }, [isRecording]);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: { mediaSource: 'screen' },
        audio: true
      });
      
      streamRef.current = stream;
      chunksRef.current = [];
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'video/webm' });
        setRecordedBlob(blob);
        setShowMetadataForm(true);
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      intervalRef.current = setInterval(() => {
        setRecordingTime(prev => {
          if (prev >= 900) {
            stopRecording();
            return prev;
          }
          return prev + 1;
        });
      }, 1000);

    } catch (error) {
      setError('Error accessing screen: ' + error.message);
    }
  }, [stopRecording]);

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      if (isPaused) {
        mediaRecorderRef.current.resume();
        intervalRef.current = setInterval(() => {
          setRecordingTime(prev => prev + 1);
        }, 1000);
      } else {
        mediaRecorderRef.current.pause();
        clearInterval(intervalRef.current);
      }
      setIsPaused(!isPaused);
    }
  }, [isRecording, isPaused]);

  const uploadRecording = async () => {
    if (!recordedBlob || !metadata.title.trim()) {
      setError('Title is required');
      return;
    }

    try {
      setUploading(true);
      setError(null);

      const formData = new FormData();
      formData.append('video', recordedBlob, 'recording.webm');
      formData.append('title', metadata.title);
      formData.append('description', metadata.description);
      formData.append('tags', metadata.tags);
      formData.append('creator', 'Current User');
      formData.append('duration', formatTime(recordingTime));

      const response = await fetch(`${API_BASE}/api/recordings`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Upload failed: ' + response.statusText);
      }

      const newRecording = await response.json();
      setRecordings(prev => [newRecording, ...prev]);
      
      setMetadata({ title: '', description: '', tags: '' });
      setShowMetadataForm(false);
      setRecordedBlob(null);
      setRecordingTime(0);
      setCurrentView('browse');
      
    } catch (err) {
      setError('Upload failed: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const downloadRecording = async (recording) => {
    try {
      const response = await fetch(`${API_BASE}/api/recordings/${recording.id}`);
      if (!response.ok) throw new Error('Failed to get download URL');
      
      const data = await response.json();
      if (data.video_url) {
        const a = document.createElement('a');
        a.href = data.video_url;
        a.download = `${recording.title.replace(/[^a-z0-9]/gi, '_')}.webm`;
        a.click();
      }
    } catch (err) {
      setError('Download failed: ' + err.message);
    }
  };

  const filteredRecordings = recordings.filter(recording => {
    const matchesSearch = recording.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         recording.creator?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTags = selectedTags.length === 0 || 
                       selectedTags.some(tag => recording.tags?.includes(tag));
    return matchesSearch && matchesTags;
  });

  const allTags = [...new Set(recordings.flatMap(r => r.tags || []))];

  if (showMetadataForm) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold mb-6">Add Recording Details</h2>
          
          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-300 rounded-lg flex items-center gap-2">
              <AlertCircle size={20} className="text-red-600" />
              <span className="text-red-800">{error}</span>
            </div>
          )}
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Title *</label>
              <input
                type="text"
                value={metadata.title}
                onChange={(e) => setMetadata(prev => ({ ...prev, title: e.target.value }))}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Descriptive title for your recording"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Description</label>
              <textarea
                value={metadata.description}
                onChange={(e) => setMetadata(prev => ({ ...prev, description: e.target.value }))}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                rows="3"
                placeholder="Brief description of what you recorded"
                maxLength="500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Tags</label>
              <input
                type="text"
                value={metadata.tags}
                onChange={(e) => setMetadata(prev => ({ ...prev, tags: e.target.value }))}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Comma-separated tags (e.g., API, React, Tutorial)"
              />
            </div>
            
            <div className="flex gap-3 pt-4">
              <button
                onClick={uploadRecording}
                disabled={uploading}
                className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 font-medium disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload size={20} />
                    Save Recording
                  </>
                )}
              </button>
              <button
                onClick={() => setShowMetadataForm(false)}
                disabled={uploading}
                className="px-6 py-3 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Knowledge Harvest</h1>
            <nav className="flex gap-4">
              <button
                onClick={() => setCurrentView('record')}
                className={`px-4 py-2 rounded-lg font-medium ${currentView === 'record' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:text-gray-900'}`}
              >
                Record
              </button>
              <button
                onClick={() => setCurrentView('browse')}
                className={`px-4 py-2 rounded-lg font-medium ${currentView === 'browse' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:text-gray-900'}`}
              >
                Browse
              </button>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {error && !showMetadataForm && (
          <div className="mb-6 p-3 bg-red-100 border border-red-300 rounded-lg flex items-center gap-2">
            <AlertCircle size={20} className="text-red-600" />
            <span className="text-red-800">{error}</span>
            <button 
              onClick={() => setError(null)}
              className="ml-auto text-red-600 hover:text-red-800"
            >
              ×
            </button>
          </div>
        )}

        {currentView === 'record' && (
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-lg shadow-lg p-8 text-center">
              <h2 className="text-2xl font-bold mb-6">Screen Recording</h2>
              
              {!isRecording ? (
                <div>
                  <p className="text-gray-600 mb-6">
                    Click start to begin recording your screen and audio. Maximum duration is 15 minutes.
                  </p>
                  <button
                    onClick={startRecording}
                    className="bg-red-600 hover:bg-red-700 text-white px-8 py-4 rounded-lg font-medium flex items-center gap-2 mx-auto"
                  >
                    <Play size={20} />
                    Start Recording
                  </button>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="text-4xl font-mono text-red-600">
                    {formatTime(recordingTime)}
                  </div>
                  
                  {recordingTime >= 780 && (
                    <div className="bg-orange-100 border border-orange-300 rounded-lg p-3">
                      <p className="text-orange-800">Recording will stop automatically at 15 minutes</p>
                    </div>
                  )}
                  
                  <div className="flex gap-4 justify-center">
                    <button
                      onClick={pauseRecording}
                      className="bg-yellow-600 hover:bg-yellow-700 text-white px-6 py-3 rounded-lg font-medium flex items-center gap-2"
                    >
                      <Pause size={20} />
                      {isPaused ? 'Resume' : 'Pause'}
                    </button>
                    <button
                      onClick={stopRecording}
                      className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-medium flex items-center gap-2"
                    >
                      <Square size={20} />
                      Stop Recording
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {currentView === 'browse' && (
          <div>
            <div className="flex gap-4 mb-6">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-3 text-gray-400" size={20} />
                <input
                  type="text"
                  placeholder="Search recordings..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="relative">
                <select
                  value={selectedTags[0] || ''}
                  onChange={(e) => setSelectedTags(e.target.value ? [e.target.value] : [])}
                  className="pl-10 pr-8 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 appearance-none bg-white"
                >
                  <option value="">All Tags</option>
                  {allTags.map(tag => (
                    <option key={tag} value={tag}>{tag}</option>
                  ))}
                </select>
                <Filter className="absolute left-3 top-3 text-gray-400 pointer-events-none" size={20} />
              </div>
            </div>

            {loading && (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            )}

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {filteredRecordings.map(recording => (
                <div key={recording.id} className="bg-white rounded-lg shadow-lg overflow-hidden">
                  <div className="aspect-video bg-gray-200 flex items-center justify-center">
                    <Play size={48} className="text-gray-400" />
                  </div>
                  <div className="p-4">
                    <h3 className="font-semibold text-lg mb-2">{recording.title}</h3>
                    <p className="text-gray-600 text-sm mb-3">
                      By {recording.creator} • {new Date(recording.created_at).toLocaleDateString()} • {typeof recording.duration === 'string' ? recording.duration : 'Unknown'}
                    </p>
                    <div className="flex flex-wrap gap-1 mb-4">
                      {(recording.tags || []).map(tag => (
                        <span key={tag} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                          {tag}
                        </span>
                      ))}
                    </div>
                    <div className="flex gap-2">
                      <button className="flex-1 bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 flex items-center justify-center gap-2">
                        <Play size={16} />
                        Watch
                      </button>
                      <button
                        onClick={() => downloadRecording(recording)}
                        className="p-2 border rounded hover:bg-gray-50"
                      >
                        <Download size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {!loading && filteredRecordings.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg">No recordings found</p>
                <button
                  onClick={() => setCurrentView('record')}
                  className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
                >
                  Create your first recording
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default KnowledgeHarvestApp;
