import React, { useState, useEffect } from 'react';
import { ArrowLeft, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { ApiService } from '../utils/apiService';

interface ZKProofScreenProps {
  score: number;
  onBack: () => void;
}

const ZKProofScreen: React.FC<ZKProofScreenProps> = ({ score, onBack }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmitScore = async () => {
    setIsSubmitting(true);
    setError(null);
    
    try {
      const playerId = ApiService.generatePlayerId();
      const result = await ApiService.submitScore({
        player_id: playerId,
        score: score,
        difficulty: 1
      });
      
      setSubmissionResult(result);
      console.log('✅ Score submitted successfully:', result);
    } catch (err: any) {
      setError(err.message || 'Failed to submit score');
      console.error('❌ Error submitting score:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    if (score > 0) {
      handleSubmitScore();
    }
  }, [score]);

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
              <h3 className="font-semibold text-gray-800 mb-2">Proof Generation Status:</h3>
              <div className="text-sm text-gray-600">
                <p>• Proof Hash: {submissionResult.score_data?.proof_hash}</p>
                <p>• Status: {submissionResult.proof_status}</p>
                <p>• Estimated Time: {submissionResult.estimated_time}</p>
              </div>
            </div>
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
              Your score is being cryptographically proven using Zero-Knowledge Proofs. 
              This process involves:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Building the program with your score</li>
              <li>Compiling with ZisK</li>
              <li>Setting up the execution environment</li>
              <li>Running the program</li>
              <li>Generating the cryptographic proof</li>
              <li>Verifying the proof</li>
            </ul>
            <p className="mt-4 text-sm text-gray-500">
              This process typically takes 15-20 minutes. The proof will be generated in the background.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ZKProofScreen;