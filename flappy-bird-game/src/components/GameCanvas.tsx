import React, { useRef, useEffect } from 'react';
import { Bird, Pipe } from '../types/game';
import { GAME_CONFIG } from '../utils/gamePhysics';

interface GameCanvasProps {
  bird: Bird;
  pipes: Pipe[];
  gameStatus: 'menu' | 'playing' | 'gameOver' | 'proof';
  score: number;
}

export const GameCanvas: React.FC<GameCanvasProps> = ({ bird, pipes, gameStatus, score }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas with gradient background
    const gradient = ctx.createLinearGradient(0, 0, 0, GAME_CONFIG.CANVAS_HEIGHT);
    gradient.addColorStop(0, '#FFE4E6');
    gradient.addColorStop(0.5, '#FDF2F8');
    gradient.addColorStop(1, '#F0F9FF');
    
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, GAME_CONFIG.CANVAS_WIDTH, GAME_CONFIG.CANVAS_HEIGHT);

    // Draw clouds
    drawClouds(ctx);

    // Draw ground
    drawGround(ctx);

    // Draw pipes
    pipes.forEach(pipe => drawPipe(ctx, pipe));

    // Draw bird
    drawBird(ctx, bird, gameStatus);

    // Draw score effects
    if (gameStatus === 'playing') {
      drawScoreEffect(ctx, score);
    }

  }, [bird, pipes, gameStatus, score]);

  const drawBird = (ctx: CanvasRenderingContext2D, bird: Bird, gameStatus: string) => {
    ctx.save();
    ctx.translate(bird.x, bird.y);
    ctx.rotate((bird.rotation * Math.PI) / 180);

    // Add subtle bounce animation when jumping
    const bounceScale = gameStatus === 'playing' && bird.velocity < -3 ? 1.1 : 1.0;
    ctx.scale(bounceScale, bounceScale);

    // Bird body gradient
    const gradient = ctx.createRadialGradient(0, 0, 5, 0, 0, GAME_CONFIG.BIRD_SIZE / 2);
    gradient.addColorStop(0, '#FBBF24');
    gradient.addColorStop(1, '#F59E0B');

    // Bird body
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(0, 0, GAME_CONFIG.BIRD_SIZE / 2, 0, Math.PI * 2);
    ctx.fill();

    // Bird wing
    ctx.fillStyle = '#FCD34D';
    ctx.beginPath();
    ctx.ellipse(-8, 0, 8, 12, 0, 0, Math.PI * 2);
    ctx.fill();

    // Bird eye
    ctx.fillStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.arc(5, -5, 4, 0, Math.PI * 2);
    ctx.fill();

    // Bird pupil
    ctx.fillStyle = '#000000';
    ctx.beginPath();
    ctx.arc(6, -5, 2, 0, Math.PI * 2);
    ctx.fill();

    // Bird beak
    ctx.fillStyle = '#FB923C';
    ctx.beginPath();
    ctx.moveTo(12, 0);
    ctx.lineTo(20, -2);
    ctx.lineTo(20, 2);
    ctx.closePath();
    ctx.fill();

    ctx.restore();
  };

  const drawGround = (ctx: CanvasRenderingContext2D) => {
    const groundY = GAME_CONFIG.CANVAS_HEIGHT - GAME_CONFIG.GROUND_HEIGHT;
    
    // Ground gradient
    const gradient = ctx.createLinearGradient(0, groundY, 0, GAME_CONFIG.CANVAS_HEIGHT);
    gradient.addColorStop(0, '#10B981');
    gradient.addColorStop(1, '#047857');
    
    ctx.fillStyle = gradient;
    ctx.fillRect(0, groundY, GAME_CONFIG.CANVAS_WIDTH, GAME_CONFIG.GROUND_HEIGHT);
    
    // Ground pattern
    ctx.fillStyle = '#065F46';
    for (let x = 0; x < GAME_CONFIG.CANVAS_WIDTH; x += 20) {
      ctx.fillRect(x, groundY, 2, GAME_CONFIG.GROUND_HEIGHT);
    }
  };

  const drawScoreEffect = (ctx: CanvasRenderingContext2D, score: number) => {
    if (score > 0) {
      // Subtle sparkle effect for scoring
      const sparkles = 3;
      for (let i = 0; i < sparkles; i++) {
        const x = Math.random() * GAME_CONFIG.CANVAS_WIDTH;
        const y = Math.random() * GAME_CONFIG.CANVAS_HEIGHT * 0.7;
        const size = Math.random() * 3 + 1;
        
        ctx.fillStyle = `rgba(255, 215, 0, ${Math.random() * 0.5 + 0.3})`;
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  };

  const drawPipe = (ctx: CanvasRenderingContext2D, pipe: Pipe) => {
    // Pipe gradient
    const gradient = ctx.createLinearGradient(pipe.x, 0, pipe.x + GAME_CONFIG.PIPE_WIDTH, 0);
    gradient.addColorStop(0, '#10B981');
    gradient.addColorStop(0.5, '#059669');
    gradient.addColorStop(1, '#047857');

    // Top pipe
    ctx.fillStyle = gradient;
    ctx.fillRect(pipe.x, 0, GAME_CONFIG.PIPE_WIDTH, pipe.topHeight);
    
    // Top pipe cap
    ctx.fillStyle = '#065F46';
    ctx.fillRect(pipe.x - 5, pipe.topHeight - 20, GAME_CONFIG.PIPE_WIDTH + 10, 20);

    // Bottom pipe
    ctx.fillRect(pipe.x, GAME_CONFIG.CANVAS_HEIGHT - pipe.bottomHeight, GAME_CONFIG.PIPE_WIDTH, pipe.bottomHeight);
    
    // Bottom pipe cap
    ctx.fillRect(pipe.x - 5, GAME_CONFIG.CANVAS_HEIGHT - pipe.bottomHeight, GAME_CONFIG.PIPE_WIDTH + 10, 20);
  };

  const drawClouds = (ctx: CanvasRenderingContext2D) => {
    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
    
    // Cloud 1
    drawCloud(ctx, 80, 100, 0.8);
    drawCloud(ctx, 250, 80, 0.6);
    drawCloud(ctx, 320, 150, 0.7);
  };

  const drawCloud = (ctx: CanvasRenderingContext2D, x: number, y: number, scale: number) => {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(scale, scale);
    
    ctx.beginPath();
    ctx.arc(0, 0, 15, 0, Math.PI * 2);
    ctx.arc(15, 0, 20, 0, Math.PI * 2);
    ctx.arc(30, 0, 15, 0, Math.PI * 2);
    ctx.arc(15, -15, 15, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.restore();
  };

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        width={GAME_CONFIG.CANVAS_WIDTH}
        height={GAME_CONFIG.CANVAS_HEIGHT}
        className="rounded-3xl shadow-2xl border-4 border-white/50 bg-gradient-to-b from-pink-100 via-purple-50 to-blue-50"
      />
    </div>
  );
};