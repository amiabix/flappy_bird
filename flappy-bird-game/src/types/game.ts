export interface Bird {
  x: number;
  y: number;
  velocity: number;
  rotation: number;
}

export interface Pipe {
  x: number;
  topHeight: number;
  bottomHeight: number;
  passed: boolean;
  id: number;
}

export interface GameState {
  bird: Bird;
  pipes: Pipe[];
  score: number;
  gameStatus: 'menu' | 'playing' | 'gameOver' | 'proof';
  highScore: number;
  currentSessionId?: string | null; // Current game session ID for ZisK proof generation
}

export interface ZKProof {
  score: number;
  timestamp: number;
  proof: string;
  publicInputs: {
    finalScore: number;
    gameId: string;
    ziskOutput?: string;
    buildOutput?: string;
    cargoOutput?: string;
    romSetupOutput?: string;
    step3Output?: string;
    step4Output?: string;
    step5Output?: string;
    finalStatus?: string;
    error?: string;
  };
}