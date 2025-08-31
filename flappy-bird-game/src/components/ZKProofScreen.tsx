import React, { useState, useCallback } from 'react';
import { ArrowLeft, CheckCircle, Clock, AlertCircle, Zap, Shield, RefreshCw } from 'lucide-react';

interface ZKProofScreenProps {
  score: number;
  onBack: () => void;
  sessionId?: string | null; // Add sessionId prop
}

const ZKProofScreen: React.FC<ZKProofScreenProps> = ({ score, onBack, sessionId }) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [proofResult, setProofResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [hasGenerated, setHasGenerated] = useState(false);

  const handleGenerateProof = useCallback(async () => {
    // Prevent duplicate generation
    if (hasGenerated || isGenerating) {
      console.log('🚫 Proof already generated or generation in progress, skipping...');
      return;
    }

    setIsGenerating(true);
    setError(null);
    
    try {
      // Generate ZisK proof using the real system
      // This will create a session, simulate gameplay, and generate proof
      const result = await generateZisKProof(score);
      
      setProofResult(result);
      console.log('✅ ZisK proof generated successfully:', result);
      setHasGenerated(true);
      
    } catch (err: any) {
      setError(err.message || 'Failed to generate ZisK proof');
      console.error('❌ Error generating ZisK proof:', err);
      setHasGenerated(false); // Reset on error to allow retry
    } finally {
      setIsGenerating(false);
    }
  }, [score, hasGenerated, isGenerating]);

  // Function to generate ZisK proof using the real backend system
  const generateZisKProof = async (score: number) => {
    try {
      // Use the new direct ZisK proof generation endpoint
      const response = await fetch('http://localhost:5000/api/generate-zisk-proof', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          score: score,
          player_id: `player_${Date.now()}`
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to generate ZisK proof');
      }
      
      const result = await response.json();
      console.log('✅ ZisK proof generated successfully:', result);
      
      return {
        success: true,
        proof_id: result.proof_id,
        proof_queued: true,
        message: result.message,
        proof_file: result.proof_file,
        proof_size: result.proof_size
      };
      
    } catch (error: any) {
      throw new Error(`ZisK proof generation failed: ${error.message}`);
    }
  };



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
          <h1 className="text-3xl font-bold text-gray-800">🔐 ZisK Proof Generation</h1>
        </div>

        {/* Score Display */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 text-center">
          <div className="text-6xl font-bold text-purple-600 mb-4">{score}</div>
          <div className="text-xl text-gray-600">Points to Prove</div>
        </div>

        {/* Main Content */}
        <div className="grid md:grid-cols-2 gap-8">
          {/* Left Column - Proof Generation */}
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="flex items-center mb-6">
              <Zap className="w-8 h-8 text-purple-600 mr-3" />
              <h2 className="text-2xl font-bold text-gray-800">Generate ZisK Proof</h2>
            </div>
            
            <p className="text-gray-600 mb-6">
              Generate a cryptographic proof that validates your score using the ZisK zero-knowledge system.
              This proof proves your score is legitimate without revealing gameplay details.
            </p>

            {!hasGenerated ? (
              <button
                onClick={handleGenerateProof}
                disabled={isGenerating}
                className={`w-full py-4 px-6 rounded-xl font-bold text-lg transition-all duration-300 ${
                  isGenerating
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white shadow-lg hover:shadow-xl transform hover:scale-105'
                }`}
              >
                {isGenerating ? (
                  <div className="flex items-center justify-center">
                    <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                    Generating Proof...
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    <Zap className="w-5 h-5 mr-2" />
                    Generate ZisK Proof
                  </div>
                )}
              </button>
            ) : (
              <div className="text-center">
                <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-green-600 mb-2">Proof Generated!</h3>
                <p className="text-gray-600">Your ZisK proof has been created successfully.</p>
              </div>
            )}

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl">
                <div className="flex items-center">
                  <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                  <span className="text-red-700">{error}</span>
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Proof Details */}
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="flex items-center mb-6">
              <Shield className="w-8 h-8 text-blue-600 mr-3" />
              <h2 className="text-2xl font-bold text-gray-800">Proof Details</h2>
            </div>

            {!hasGenerated ? (
              <div className="text-center text-gray-500 py-12">
                <Clock className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>No proof generated yet</p>
                <p className="text-sm">Click "Generate ZisK Proof" to start</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                  <div className="flex items-center mb-2">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                    <span className="font-semibold text-green-700">Status: Success</span>
                  </div>
                  <p className="text-green-600 text-sm">{proofResult?.message}</p>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                  <h4 className="font-semibold text-blue-700 mb-2">Proof Information</h4>
                  <div className="text-sm text-blue-600 space-y-1">
                    <p><strong>Proof ID:</strong> {proofResult?.proof_id}</p>
                    <p><strong>Score:</strong> {score} points</p>
                    <p><strong>Proof File:</strong> {proofResult?.proof_file}</p>
                    <p><strong>Proof Size:</strong> {proofResult?.proof_size} bytes</p>
                  </div>
                </div>

                <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
                  <h4 className="font-semibold text-purple-700 mb-2">What This Means</h4>
                  <ul className="text-sm text-purple-600 space-y-1">
                    <li>• Your score is cryptographically verified</li>
                    <li>• Proof generated using ZisK zero-knowledge system</li>
                    <li>• Gameplay data is validated without revealing details</li>
                    <li>• Score is now tamper-proof and verifiable</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500">
          <p className="text-sm">
            ZisK Proof System • Zero-Knowledge Score Verification • Anti-Cheat Protection
          </p>
        </div>
      </div>
    </div>
  );
};

export default ZKProofScreen;