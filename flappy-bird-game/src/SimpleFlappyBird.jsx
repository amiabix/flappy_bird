import React, { useState, useEffect, useRef } from "react";

export default function SimpleFlappyBird() {
  const [birdPosition, setBirdPosition] = useState(250);
  const [gameStarted, setGameStarted] = useState(false);
  const [pipes, setPipes] = useState([]);
  const [score, setScore] = useState(0);
  const [gameOver, setGameOver] = useState(false);
  const [clouds, setClouds] = useState([]);
  const [difficulty, setDifficulty] = useState(1);
  const [highScore, setHighScore] = useState(0);

  const gameHeight = 600;
  const gameWidth = 400;
  const gravity = 6;
  const jumpHeight = 80;
  const pipeWidth = 60;
  const pipeGap = 150;
  const cloudWidth = 80;

  const gameLoopRef = useRef(null);

  // Gravity loop
  useEffect(() => {
    if (gameStarted && !gameOver) {
      gameLoopRef.current = setInterval(() => {
        setBirdPosition((prev) => Math.min(prev + gravity, gameHeight - 30));
      }, 24);
    }
    return () => clearInterval(gameLoopRef.current);
  }, [gameStarted, gameOver]);

  // Pipes movement
  useEffect(() => {
    if (gameStarted && !gameOver) {
      const pipeInterval = setInterval(() => {
        setPipes((prev) => {
          let newPipes = prev.map((pipe) => ({ ...pipe, x: pipe.x - 5 }));
          if (newPipes.length === 0 || newPipes[newPipes.length - 1].x < gameWidth - 200) {
            const topHeight = Math.floor(Math.random() * (gameHeight - pipeGap - 100)) + 50;
            newPipes.push({ x: gameWidth, topHeight });
          }
          return newPipes.filter((pipe) => pipe.x + pipeWidth > 0);
        });
      }, 50);
      return () => clearInterval(pipeInterval);
    }
  }, [gameStarted, gameOver]);

  // Clouds movement (background layer)
  useEffect(() => {
    if (gameStarted && !gameOver) {
      const cloudInterval = setInterval(() => {
        setClouds((prev) => {
          let newClouds = prev.map((cloud) => ({ ...cloud, x: cloud.x - cloud.speed }));
          if (newClouds.length === 0 || newClouds[newClouds.length - 1].x < gameWidth - 150) {
            newClouds.push({ x: gameWidth, y: Math.random() * 200, speed: 1 + Math.random() * 2 });
          }
          return newClouds.filter((cloud) => cloud.x + cloudWidth > 0);
        });
      }, 50);
      return () => clearInterval(cloudInterval);
    }
  }, [gameStarted, gameOver]);

  // Collision detection
  useEffect(() => {
    pipes.forEach((pipe) => {
      const birdWithinPipeX = pipe.x < 50 && pipe.x + pipeWidth > 20;
      const birdHitPipe =
        birdPosition < pipe.topHeight || birdPosition > pipe.topHeight + pipeGap;
      if (birdWithinPipeX && birdHitPipe) {
        setGameOver(true);
        setGameStarted(false);
      }
      if (pipe.x + pipeWidth === 20) {
        setScore((prev) => prev + 1);
      }
    });
  }, [pipes, birdPosition]);

  const handleJump = () => {
    if (!gameStarted) {
      setGameStarted(true);
      setGameOver(false);
      setPipes([]);
      setClouds([]);
      setScore(0);
      setBirdPosition(250);
    } else {
      setBirdPosition((prev) => Math.max(prev - jumpHeight, 0));
    }
  };

  // Update high score when game ends
  useEffect(() => {
    if (gameOver && score > highScore) {
      setHighScore(score);
    }
  }, [gameOver, score, highScore]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.code === "Space") {
        handleJump();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  });

  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '16px',
    padding: '16px'
  };

  const controlsStyle = {
    display: 'flex',
    gap: '16px',
    alignItems: 'center'
  };

  const selectStyle = {
    border: '1px solid #ccc',
    borderRadius: '4px',
    padding: '4px 8px'
  };

  const highScoreStyle = {
    fontSize: '18px',
    fontWeight: 'bold'
  };

  const gameContainerStyle = {
    position: 'relative',
    overflow: 'hidden',
    margin: '0 auto',
    border: '4px solid black',
    borderRadius: '12px',
    cursor: 'pointer',
    width: gameWidth,
    height: gameHeight,
    background: 'skyblue'
  };

  const cloudStyle = {
    position: 'absolute',
    background: 'white',
    borderRadius: '50%',
    opacity: 0.8
  };

  const pipeStyle = {
    position: 'absolute',
    background: '#059669'
  };

  const birdStyle = {
    position: 'absolute',
    borderRadius: '50%',
    background: '#fbbf24',
    border: '2px solid #ea580c',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
  };

  const scoreStyle = {
    position: 'absolute',
    top: '8px',
    left: '50%',
    transform: 'translateX(-50%)',
    fontSize: '24px',
    fontWeight: 'bold',
    color: 'white',
    textShadow: '2px 2px 4px rgba(0, 0, 0, 0.5)'
  };

  const gameOverStyle = {
    position: 'absolute',
    inset: 0,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'rgba(0, 0, 0, 0.5)',
    zIndex: 10
  };

  const restartButtonStyle = {
    padding: '8px 24px',
    background: '#fbbf24',
    borderRadius: '12px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    color: 'black',
    fontWeight: 'bold',
    border: 'none',
    cursor: 'pointer'
  };

  const groundStyle = {
    position: 'absolute',
    bottom: 0,
    left: 0,
    width: '100%',
    height: '40px',
    background: '#047857',
    zIndex: 3
  };

  const instructionsStyle = {
    textAlign: 'center',
    color: '#666',
    maxWidth: '400px'
  };

  return (
    <div style={containerStyle}>
      {/* Game Controls */}
      <div style={controlsStyle}>
        <div style={controlsStyle}>
          <label style={{ fontSize: '14px', fontWeight: '500' }}>Difficulty:</label>
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(Number(e.target.value))}
            style={selectStyle}
            disabled={gameStarted}
          >
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(level => (
              <option key={level} value={level}>Level {level}</option>
            ))}
          </select>
        </div>
        
        <div style={highScoreStyle}>
          High Score: {highScore}
        </div>
      </div>

      {/* Game Container */}
      <div
        style={gameContainerStyle}
        onClick={handleJump}
      >
        {/* Clouds in background */}
        {clouds.map((cloud, i) => (
          <div
            key={i}
            style={{
              ...cloudStyle,
              width: cloudWidth,
              height: 40,
              left: cloud.x,
              top: cloud.y,
              zIndex: 0,
            }}
          />
        ))}

        {/* Pipes */}
        {pipes.map((pipe, i) => (
          <React.Fragment key={i}>
            <div
              style={{
                ...pipeStyle,
                width: pipeWidth,
                height: pipe.topHeight,
                left: pipe.x,
                top: 0,
                zIndex: 1
              }}
            />
            <div
              style={{
                ...pipeStyle,
                width: pipeWidth,
                height: gameHeight - pipe.topHeight - pipeGap,
                left: pipe.x,
                top: pipe.topHeight + pipeGap,
                zIndex: 1
              }}
            />
          </React.Fragment>
        ))}

        {/* Bird */}
        <div
          style={{
            ...birdStyle,
            width: 30,
            height: 30,
            left: 20,
            top: birdPosition,
            zIndex: 2
          }}
        />

        {/* Score */}
        <div style={scoreStyle}>
          {score}
        </div>

        {/* Game Over UI */}
        {gameOver && (
          <div style={gameOverStyle}>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: 'white', marginBottom: '16px' }}>
              Game Over
            </div>
            <div style={{ fontSize: '20px', color: 'white', marginBottom: '16px' }}>
              Final Score: {score}
            </div>
            
            <button
              onClick={handleJump}
              style={restartButtonStyle}
            >
              Restart
            </button>
          </div>
        )}

        {/* Ground */}
        <div style={groundStyle} />
      </div>

      {/* Instructions */}
      <div style={instructionsStyle}>
        <p style={{ marginBottom: '8px' }}>Click or press Space to make the bird jump</p>
        <p style={{ fontSize: '14px' }}>Avoid the pipes and try to get the highest score!</p>
      </div>
    </div>
  );
}
