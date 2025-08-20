import React, { useState, useEffect, useCallback } from 'react';
import { GameState } from '../types/game';
import { 
  updateBird, 
  jumpBird, 
  updatePipes, 
  generatePipe, 
  checkCollision, 
  updateScore,
  GAME_CONFIG 
} from '../utils/gamePhysics';
import { ApiService } from '../utils/apiService';
import { GameCanvas } from './GameCanvas';
import { GameOverlay } from './GameOverlay';
import { ZKProofScreen } from './ZKProofScreen';

export const FlappyBirdGame: React.FC = () => {
  const [gameState, setGameState] = useState<GameState>({
    bird: {
      x: GAME_CONFIG.CANVAS_WIDTH * 0.3,
      y: GAME_CONFIG.CANVAS_HEIGHT / 2,
      velocity: 0,
      rotation: 0,
    },
    pipes: [],
    score: 0,
    gameStatus: 'menu',
    highScore: parseInt(localStorage.getItem('flappyHighScore') || '0'),
  });

  const [frameCount, setFrameCount] = useState(0);
  const [pipeId, setPipeId] = useState(0);
  const [gameSpeed, setGameSpeed] = useState(1);
  const [particles, setParticles] = useState<Array<{x: number, y: number, life: number}>>([]);
  const [playerId] = useState(() => {
    // Get existing player ID from localStorage or generate new one
    const existingId = localStorage.getItem('flappyPlayerId');
    if (existingId) return existingId;
    
    const newId = ApiService.generatePlayerId();
    localStorage.setItem('flappyPlayerId', newId);
    return newId;
  });

  // Game loop
  useEffect(() => {
    if (gameState.gameStatus !== 'playing') return;

    const gameLoop = setInterval(() => {
      setGameState(prevState => {
        if (prevState.gameStatus !== 'playing') return prevState;

        // Gradually increase game speed
        const newSpeed = Math.min(1.5, 1 + prevState.score * 0.01);
        setGameSpeed(newSpeed);

        // Update bird
        const updatedBird = updateBird(prevState.bird);

        // Update pipes
        let updatedPipes = updatePipes(prevState.pipes);

        // Generate new pipes
        const adjustedSpawnRate = Math.max(80, GAME_CONFIG.PIPE_SPAWN_RATE - prevState.score * 2);
        if (frameCount % adjustedSpawnRate === 0) {
          updatedPipes.push(generatePipe(pipeId));
          setPipeId(prev => prev + 1);
        }

        // Update score
        const { newPipes, scoreIncrease } = updateScore(updatedBird, updatedPipes);
        updatedPipes = newPipes;
        const newScore = prevState.score + scoreIncrease;

        // Add particle effect when scoring
        if (scoreIncrease > 0) {
          setParticles(prev => [...prev, 
            ...Array.from({length: 5}, (_, i) => ({
              x: updatedBird.x + Math.random() * 40 - 20,
              y: updatedBird.y + Math.random() * 40 - 20,
              life: 30
            }))
          ]);
        }

        // Check collision
        if (checkCollision(updatedBird, updatedPipes)) {
          const finalHighScore = Math.max(newScore, prevState.highScore);
          localStorage.setItem('flappyHighScore', finalHighScore.toString());
          
          // Automatically submit score to API when game ends
          if (newScore > 0) {
            ApiService.submitScore({
              player_id: playerId,
              score: newScore,
              difficulty: 1
            }).then(success => {
              if (success) {
                console.log(`🎯 Score ${newScore} submitted to API successfully!`);
              } else {
                console.log('⚠️ Score submission failed, but game continues');
              }
            });
          }
          
          return {
            ...prevState,
            bird: updatedBird,
            pipes: updatedPipes,
            score: newScore,
            gameStatus: 'gameOver',
            highScore: finalHighScore,
          };
        }

        return {
          ...prevState,
          bird: updatedBird,
          pipes: updatedPipes,
          score: newScore,
        };
      });

      setFrameCount(prev => prev + 1);
      
      // Update particles
      setParticles(prev => prev
        .map(p => ({ ...p, life: p.life - 1 }))
        .filter(p => p.life > 0)
      );
      
    }, 1000 / 60); // 60 FPS

    return () => clearInterval(gameLoop);
  }, [gameState.gameStatus, frameCount, pipeId, gameSpeed]);

  // Handle jump
  const handleJump = useCallback(() => {
    if (gameState.gameStatus === 'playing') {
      setGameState(prevState => ({
        ...prevState,
        bird: jumpBird(prevState.bird),
      }));
    }
  }, [gameState.gameStatus]);

  // Keyboard controls
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.code === 'Space' || e.code === 'ArrowUp') {
        e.preventDefault();
        handleJump();
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [handleJump]);

  const startGame = () => {
    setGameState(prevState => ({
      ...prevState,
      bird: {
        x: GAME_CONFIG.CANVAS_WIDTH * 0.3,
        y: GAME_CONFIG.CANVAS_HEIGHT / 2,
        velocity: 0,
        rotation: 0,
      },
      pipes: [],
      score: 0,
      gameStatus: 'playing',
    }));
    setFrameCount(0);
    setPipeId(0);
  };

  const restartGame = () => {
    startGame();
  };

  const generateProof = () => {
    setGameState(prevState => ({
      ...prevState,
      gameStatus: 'proof',
    }));
  };

  const backToMenu = () => {
    setGameState(prevState => ({
      ...prevState,
      gameStatus: 'menu',
    }));
  };

  // Manual score submission for existing scores
  const submitCurrentScore = async () => {
    const currentHighScore = parseInt(localStorage.getItem('flappyHighScore') || '0');
    if (currentHighScore > 0) {
      const success = await ApiService.submitScore({
        player_id: playerId,
        score: currentHighScore,
        difficulty: 1
      });
      
      if (success) {
        console.log(`🎯 Current high score ${currentHighScore} submitted to API!`);
        // Refresh leaderboard
        const data = await ApiService.getLeaderboard(1);
        if (data) {
          setLeaderboard(data);
        }
      } else {
        console.log('⚠️ Failed to submit current score');
      }
    }
  };

  // Fetch leaderboard data
  const [leaderboard, setLeaderboard] = useState<any>(null);
  
  useEffect(() => {
    const fetchLeaderboard = async () => {
      const data = await ApiService.getLeaderboard(1);
      if (data) {
        setLeaderboard(data);
      }
    };
    
    // Fetch leaderboard when component mounts and when game status changes
    if (gameState.gameStatus === 'menu' || gameState.gameStatus === 'gameOver') {
      fetchLeaderboard();
    }
  }, [gameState.gameStatus]);

  if (gameState.gameStatus === 'proof') {
    return <ZKProofScreen score={gameState.score} onBack={backToMenu} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-100 via-purple-50 to-blue-100 flex items-center justify-center p-4">
      <div className="relative">
        {/* Score display */}
        {gameState.gameStatus === 'playing' && (
          <div className="absolute -top-20 left-1/2 transform -translate-x-1/2 z-20">
            <div className="bg-white/95 backdrop-blur-md px-8 py-4 rounded-3xl shadow-xl border-2 border-white/50 transition-all duration-300">
              <div className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent animate-pulse">
                {gameState.score}
              </div>
              {gameSpeed > 1.2 && (
                <div className="text-xs text-orange-500 font-semibold mt-1">
                  SPEED BOOST! 🚀
                </div>
              )}
            </div>
          </div>
        )}

        {/* Game canvas */}
        <div 
          onClick={handleJump}
          className="cursor-pointer select-none transition-transform hover:scale-105"
        >
          <GameCanvas
            bird={gameState.bird}
            pipes={gameState.pipes}
            gameStatus={gameState.gameStatus}
            score={gameState.score}
          />
        </div>

        {/* Game overlay */}
        <GameOverlay
          gameStatus={gameState.gameStatus}
          score={gameState.score}
          highScore={gameState.highScore}
          leaderboard={leaderboard}
          onStart={startGame}
          onRestart={restartGame}
          onGenerateProof={generateProof}
          onSubmitCurrentScore={submitCurrentScore}
        />

        {/* Instructions */}
        <div className="absolute -bottom-20 left-1/2 transform -translate-x-1/2 text-center">
          <p className="text-gray-600 text-sm">
            {gameState.gameStatus === 'playing' 
              ? 'Tap or press SPACE to fly • Game gets faster as you score!' 
              : 'Click anywhere to start playing!'}
          </p>
          {gameState.gameStatus === 'menu' && (
            <p className="text-gray-500 text-xs mt-1">
              Generate cryptographic proof of your high scores
            </p>
          )}
        </div>
      </div>
    </div>
  );
};