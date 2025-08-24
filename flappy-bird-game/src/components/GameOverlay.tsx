import React from 'react';
import { Play, RotateCcw, Trophy, Zap, Star, Award } from 'lucide-react';

interface GameOverlayProps {
  gameStatus: 'menu' | 'playing' | 'gameOver' | 'proof';
  score: number;
  highScore: number;
  leaderboard?: any;
  onStart: () => void;
  onRestart: () => void;
  onGenerateProof: () => void;
  onSubmitCurrentScore?: () => void;
}

export const GameOverlay: React.FC<GameOverlayProps> = ({
  gameStatus,
  score,
  highScore,
  leaderboard,
  onStart,
  onRestart,
  onGenerateProof,
  onSubmitCurrentScore,
}) => {
  if (gameStatus === 'playing') return null;

  const isNewHighScore = score > 0 && score >= highScore;
  const getScoreMessage = () => {
    if (score === 0) return "Give it a try!";
    if (score < 5) return "Keep practicing!";
    if (score < 10) return "Getting better!";
    if (score < 20) return "Nice flying!";
    if (score < 50) return "Impressive!";
    return "Legendary!";
  };

  return (
    <div className="absolute inset-0 flex items-center justify-center z-10">
      <div className="bg-white/95 backdrop-blur-md rounded-3xl p-8 text-center shadow-2xl border-2 border-white/50 max-w-sm mx-4 transform transition-all duration-300">
        {gameStatus === 'menu' && (
          <>
            <div className="text-6xl mb-4">🐦</div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-pink-500 via-purple-500 to-blue-500 bg-clip-text text-transparent mb-2">
              Flappy Bird with ZisK
            </h1>
            <p className="text-gray-600 mb-8">Play • Score • Prove</p>
            <button
              onClick={onStart}
              className="bg-gradient-to-r from-pink-500 to-purple-500 text-white px-8 py-4 rounded-2xl font-bold text-lg shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 flex items-center gap-2 mx-auto group"
            >
              <Play size={24} className="group-hover:scale-110 transition-transform" />
              Start Game
            </button>
            
            {/* Submit Current Score Button */}
            {onSubmitCurrentScore && highScore > 0 && (
              <button
                onClick={onSubmitCurrentScore}
                className="mt-3 bg-gradient-to-r from-green-500 to-blue-500 text-white px-6 py-3 rounded-2xl font-bold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 flex items-center gap-2 mx-auto group"
              >
                <Trophy size={20} className="group-hover:scale-110 transition-transform" />
                Submit Score: {highScore}
              </button>
            )}
          </>
        )}

        {gameStatus === 'gameOver' && (
          <>
            <div className="text-6xl mb-4">
              {isNewHighScore ? 'NEW HIGH SCORE!' : 'GAME OVER'}
            </div>
            <h2 className="text-3xl font-bold text-gray-800 mb-2">
              {isNewHighScore ? 'New High Score!' : 'Game Over!'}
            </h2>
            <p className="text-gray-600 mb-4">{getScoreMessage()}</p>
            <div className="space-y-2 mb-6">
              <div className="flex items-center justify-center gap-2">
                {isNewHighScore && <Star className="text-yellow-500" size={24} />}
                <span className="text-3xl font-bold text-purple-600">{score}</span>
                {isNewHighScore && <Star className="text-yellow-500" size={24} />}
              </div>
              <div className="flex items-center justify-center gap-2 text-lg text-gray-600">
                {isNewHighScore ? <Award size={20} className="text-yellow-600" /> : <Trophy size={20} />}
                Best: {highScore}
              </div>
            </div>
            <div className="space-y-3">
              {score > 0 && (
              <button
                onClick={onGenerateProof}
                className="bg-gradient-to-r from-purple-500 to-blue-500 text-white px-6 py-3 rounded-2xl font-bold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 flex items-center gap-2 mx-auto group"
              >
                <Zap size={20} className="group-hover:scale-110 transition-transform" />
                Generate ZisK Proof
              </button>
              )}
              <button
                onClick={onRestart}
                className="bg-gradient-to-r from-pink-500 to-purple-500 text-white px-6 py-3 rounded-2xl font-bold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 flex items-center gap-2 mx-auto group"
              >
                <RotateCcw size={20} className="group-hover:rotate-180 transition-transform duration-500" />
                Play Again
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};