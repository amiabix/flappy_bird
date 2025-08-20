import { Bird, Pipe } from '../types/game';

export const GAME_CONFIG = {
  CANVAS_WIDTH: 400,
  CANVAS_HEIGHT: 600,
  BIRD_SIZE: 30,
  PIPE_WIDTH: 60,
  PIPE_GAP: 180,
  GRAVITY: 0.4,
  JUMP_FORCE: -7.5,
  PIPE_SPEED: 3,
  PIPE_SPAWN_RATE: 120,
  MAX_VELOCITY: 10,
  GROUND_HEIGHT: 50,
};

export const updateBird = (bird: Bird): Bird => {
  const newVelocity = Math.min(GAME_CONFIG.MAX_VELOCITY, bird.velocity + GAME_CONFIG.GRAVITY);
  const newY = Math.max(GAME_CONFIG.BIRD_SIZE / 2, 
    Math.min(GAME_CONFIG.CANVAS_HEIGHT - GAME_CONFIG.GROUND_HEIGHT - GAME_CONFIG.BIRD_SIZE / 2, 
      bird.y + newVelocity));
  
  return {
    ...bird,
    y: newY,
    velocity: newVelocity,
    rotation: Math.min(45, Math.max(-25, newVelocity * 2.5)),
  };
};

export const jumpBird = (bird: Bird): Bird => ({
  ...bird,
  velocity: GAME_CONFIG.JUMP_FORCE,
  rotation: -25,
});

export const updatePipes = (pipes: Pipe[]): Pipe[] => {
  return pipes
    .map(pipe => ({ ...pipe, x: pipe.x - GAME_CONFIG.PIPE_SPEED }))
    .filter(pipe => pipe.x > -GAME_CONFIG.PIPE_WIDTH);
};

export const generatePipe = (id: number): Pipe => {
  const minHeight = 50;
  const maxHeight = GAME_CONFIG.CANVAS_HEIGHT - GAME_CONFIG.PIPE_GAP - minHeight;
  const topHeight = Math.floor(Math.random() * (maxHeight - minHeight)) + minHeight;
  
  return {
    x: GAME_CONFIG.CANVAS_WIDTH,
    topHeight,
    bottomHeight: GAME_CONFIG.CANVAS_HEIGHT - topHeight - GAME_CONFIG.PIPE_GAP,
    passed: false,
    id,
  };
};

export const checkCollision = (bird: Bird, pipes: Pipe[]): boolean => {
  // Ground and ceiling collision
  if (bird.y >= GAME_CONFIG.CANVAS_HEIGHT - GAME_CONFIG.GROUND_HEIGHT - GAME_CONFIG.BIRD_SIZE / 2 || 
      bird.y <= GAME_CONFIG.BIRD_SIZE / 2) {
    return true;
  }

  // Pipe collision
  return pipes.some(pipe => {
    const birdRadius = GAME_CONFIG.BIRD_SIZE / 2 - 2; // Slightly smaller hitbox for better feel
    const birdLeft = bird.x - birdRadius;
    const birdRight = bird.x + birdRadius;
    const birdTop = bird.y - birdRadius;
    const birdBottom = bird.y + birdRadius;

    const pipeLeft = pipe.x;
    const pipeRight = pipe.x + GAME_CONFIG.PIPE_WIDTH;

    if (birdRight > pipeLeft && birdLeft < pipeRight) {
      return birdTop < pipe.topHeight || birdBottom > GAME_CONFIG.CANVAS_HEIGHT - pipe.bottomHeight;
    }
    return false;
  });
};

export const updateScore = (bird: Bird, pipes: Pipe[]): { newPipes: Pipe[]; scoreIncrease: number } => {
  let scoreIncrease = 0;
  const newPipes = pipes.map(pipe => {
    if (!pipe.passed && pipe.x + GAME_CONFIG.PIPE_WIDTH < bird.x) {
      scoreIncrease += 1;
      return { ...pipe, passed: true };
    }
    return pipe;
  });

  return { newPipes, scoreIncrease };
};