import React, { useState, useEffect, useCallback } from 'react';
import { ArrowLeft, CheckCircle, Clock, AlertCircle, Download, RefreshCw } from 'lucide-react';
import { ApiService } from '../utils/apiService';

interface ZKProofScreenProps {
  score: number;
  onBack: () => void;
}

interface ProofStatus {
  job_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'timeout';
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  proof_file_path?: string;
  error_message?: string;
}

const ZKProofScreen: React.FC<ZKProofScreenProps> = ({ score, onBack }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [proofStatus, setProofStatus] = useState<ProofStatus | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [monitoringInterval, setMonitoringInterval] = useState<number | null>(null);
  const [hasSubmitted, setHasSubmitted] = useState(false); // NEW: Prevent duplicate submissions
  const [systemStatus, setSystemStatus] = useState<{ready: boolean, message?: string} | null>(null);

  const handleSubmitScore = useCallback(async () => {
    // Prevent duplicate submissions
    if (hasSubmitted || isSubmitting) {
      console.log('🚫 Score already submitted or submission in progress, skipping...');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setHasSubmitted(true); // Mark as submitted
    
    try {
      const playerId = ApiService.generatePlayerId();
      const result = await ApiService.submitScore({
        player_id: playerId,
        score: score,
        difficulty: 1
      });
      
      setSubmissionResult(result);
      console.log('✅ Score submitted successfully:', result);
      
      // Start monitoring the proof generation
      if (result.job_id) {
        startMonitoring(result.job_id);
      }
    } catch (err: any) {
      // Handle specific system busy error
      if (err.message && err.message.includes('System is currently busy')) {
        setError('🚫 System is currently busy generating ZisK proofs. Please try again in a few minutes.');
        console.log('🚫 System busy - user will need to wait');
      } else {
        setError(err.message || 'Failed to submit score');
        console.error('❌ Error submitting score:', err);
      }
      setHasSubmitted(false); // Reset on error to allow retry
    } finally {
      setIsSubmitting(false);
    }
  }, [score, hasSubmitted, isSubmitting]);

  const startMonitoring = (jobId: string) => {
    setIsMonitoring(true);
    
    // Initial status check
    checkProofStatus(jobId);
    
    // Set up monitoring interval (check every 10 seconds)
    const interval = setInterval(() => {
      checkProofStatus(jobId);
    }, 10000);
    
    setMonitoringInterval(interval);
  };

  const checkProofStatus = async (jobId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/proof-status/${jobId}`);
      const data = await response.json();
      
      if (data.success) {
        setProofStatus(data.job);
        
        // Stop monitoring if job is completed or failed
        if (data.job.status === 'completed' || data.job.status === 'failed' || data.job.status === 'timeout') {
          stopMonitoring();
        }
      }
    } catch (err) {
      console.error('Error checking proof status:', err);
    }
  };

  const stopMonitoring = () => {
    setIsMonitoring(false);
    if (monitoringInterval) {
      clearInterval(monitoringInterval);
      setMonitoringInterval(null);
    }
  };

  const checkSystemStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/system-status');
      if (response.ok) {
        const data = await response.json();
        setSystemStatus({
          ready: data.ready_for_submissions,
          message: data.message
        });
      } else if (response.status === 503) {
        // System is busy
        const data = await response.json();
        setSystemStatus({
          ready: false,
          message: data.message || 'System is currently busy'
        });
      }
    } catch (err) {
      console.error('Error checking system status:', err);
    }
  };

  const downloadProofFile = async () => {
    if (!proofStatus?.proof_file_path) return;
    
    try {
      // Create a download link for the proof file
      const response = await fetch(`http://localhost:8000/api/download-proof/${proofStatus.job_id}`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `zisk_proof_score_${score}.bin`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      console.error('Error downloading proof file:', err);
    }
  };

  // Check system status when component mounts
  useEffect(() => {
    checkSystemStatus();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-6 h-6 text-yellow-500" />;
      case 'in_progress':
        return <RefreshCw className="w-6 h-6 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-6 h-6 text-red-500" />;
      case 'timeout':
        return <AlertCircle className="w-6 h-6 text-orange-500" />;
      default:
        return <Clock className="w-6 h-6 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-50 border-yellow-200 text-yellow-700';
      case 'in_progress':
        return 'bg-blue-50 border-blue-200 text-blue-700';
      case 'completed':
        return 'bg-green-50 border-green-200 text-green-700';
      case 'failed':
        return 'bg-red-50 border-red-200 text-red-700';
      case 'timeout':
        return 'bg-orange-50 border-orange-200 text-orange-700';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-700';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending':
        return 'Waiting in Queue';
      case 'in_progress':
        return 'Generating ZisK Proof';
      case 'completed':
        return 'Proof Generation Complete!';
      case 'failed':
        return 'Proof Generation Failed';
      case 'timeout':
        return 'Proof Generation Timed Out';
      default:
        return 'Unknown Status';
    }
  };

  useEffect(() => {
    if (score > 0) {
      handleSubmitScore();
    }
    
    // Cleanup monitoring on unmount
    return () => {
      stopMonitoring();
    };
  }, [score, handleSubmitScore]); // Added handleSubmitScore to dependency array

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center mb-8">
          <button
            onClick={onBack}
            className="flex items-center text-gray-600 hover:text-gray-800 transition-colors mr-4"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back to Game
          </button>
          <h1 className="text-3xl font-bold text-gray-800">Proof Generation with ZisK</h1>
        </div>

        <div className="text-center mb-6">
          <h2 className="text-2xl font-semibold text-gray-700">Score: {score} points</h2>
        </div>

        {/* System Status Display */}
        {systemStatus && (
          <div className={`border rounded-lg p-4 mb-6 ${
            systemStatus.ready 
              ? 'bg-green-50 border-green-200' 
              : 'bg-orange-50 border-orange-200'
          }`}>
            <div className="flex items-center justify-center">
              {systemStatus.ready ? (
                <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
              ) : (
                <Clock className="w-5 h-5 text-orange-500 mr-2" />
              )}
              <span className={`font-medium ${
                systemStatus.ready ? 'text-green-700' : 'text-orange-700'
              }`}>
                {systemStatus.message}
              </span>
            </div>
          </div>
        )}

        {/* Status Display */}
        {isSubmitting && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
            <div className="flex items-center justify-center">
              <Clock className="w-6 h-6 text-blue-500 mr-3 animate-spin" />
              <span className="text-blue-700 text-lg">Submitting score...</span>
            </div>
          </div>
        )}

        {submissionResult && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
            <div className="flex items-center justify-center mb-4">
              <CheckCircle className="w-6 h-6 text-green-500 mr-3" />
              <span className="text-green-700 text-lg font-semibold">Score Submitted Successfully!</span>
            </div>
            <p className="text-green-600 text-center">
              Your score of {score} points has been submitted and ZisK proof generation has started.
            </p>
            <div className="mt-4 p-4 bg-white rounded-lg">
              <h3 className="font-semibold text-gray-800 mb-2">Job Details:</h3>
              <div className="text-sm text-gray-600">
                <p>• Job ID: {submissionResult.job_id}</p>
                <p>• Status: {submissionResult.proof_status}</p>
                <p>• Estimated Time: {submissionResult.estimated_time}</p>
              </div>
            </div>
          </div>
        )}

        {/* Real-time Proof Status */}
        {proofStatus && (
          <div className={`border rounded-lg p-6 mb-6 ${getStatusColor(proofStatus.status)}`}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                {getStatusIcon(proofStatus.status)}
                <span className="ml-3 text-lg font-semibold">{getStatusText(proofStatus.status)}</span>
              </div>
              {isMonitoring && (
                <div className="flex items-center text-sm">
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Monitoring...
                </div>
              )}
            </div>
            
            <div className="space-y-2 text-sm">
              {proofStatus.started_at && (
                <p>• Started: {new Date(proofStatus.started_at).toLocaleString()}</p>
              )}
              {proofStatus.duration_seconds && (
                <p>• Duration: {Math.floor(proofStatus.duration_seconds / 60)}m {proofStatus.duration_seconds % 60}s</p>
              )}
              {proofStatus.proof_file_path && (
                <p>• Proof File: {proofStatus.proof_file_path.split('/').pop()}</p>
              )}
              {proofStatus.error_message && (
                <p>• Error: {proofStatus.error_message}</p>
              )}
            </div>

            {/* Download Button for Completed Proofs */}
            {proofStatus.status === 'completed' && proofStatus.proof_file_path && (
              <div className="mt-4">
                <button
                  onClick={downloadProofFile}
                  className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg transition-colors flex items-center"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download ZisK Proof
                </button>
                <p className="text-sm text-green-600 mt-2">
                  Your cryptographic proof is ready! Download the .bin file.
                </p>
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
            <div className="flex items-center justify-center mb-4">
              <AlertCircle className="w-6 h-6 text-red-500 mr-3" />
              <span className="text-red-700 text-lg font-semibold">Submission Error</span>
            </div>
            <p className="text-red-600 text-center">{error}</p>
            <div className="mt-4 text-center">
              <button
                onClick={handleSubmitScore}
                className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {/* What's Happening Section */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">What's Happening?</h3>
          <div className="text-gray-600 space-y-3">
            <p>
              Your score is being submitted to the ZisK proof generation system. 
              This process involves:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Building the program with your score</li>
              <li>Compiling and generating the input file with ZisK</li>
              <li>Setting up the execution environment</li>
              <li>Running the program</li>
              <li>Generating the cryptographic proof with ZisK</li>
              <li>Verifying the proof</li>
            </ul>
            <p className="mt-4 text-sm text-gray-500">
              This process typically takes ~200 seconds, and the proof will be generated in the background.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ZKProofScreen;