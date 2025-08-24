# Flappy Bird Game with Zero-Knowledge Proof (ZisK) Generation

A complete implementation of the classic Flappy Bird game enhanced with cryptographic zero-knowledge proof generation using the ZisK toolchain. This project demonstrates real-time game score verification through cryptographic proofs.

## Overview

This project combines a React-based Flappy Bird game with a Flask backend API that generates cryptographic proofs for game scores using the ZisK (Zero-Knowledge) toolchain. Each game score is cryptographically verified and bound to a unique game session ID, ensuring tamper-proof verification.

## Features

- **Real Flappy Bird Game**: Classic gameplay with modern React/TypeScript implementation
- **Zero-Knowledge Proof Generation**: Real cryptographic proofs for each game score
- **Game ID Binding**: Each proof is cryptographically bound to a unique game session
- **Bulletproof Architecture**: Robust backend with worker threads and duplicate prevention
- **Real-Time Monitoring**: Live proof generation status and progress tracking
- **Production Ready**: No fake implementations, only real ZisK execution

## Architecture

### Frontend (React + TypeScript)
- **Game Engine**: Custom Flappy Bird implementation with physics
- **Proof Monitoring**: Real-time status display for ZisK proof generation
- **Score Submission**: Secure score submission with duplicate prevention
- **Modern UI**: Clean, responsive interface with real-time updates

### Backend (Flask + Python)
- **API Server**: RESTful endpoints for score submission and proof monitoring
- **Worker System**: Multi-threaded proof generation with job queuing
- **ZisK Integration**: Direct integration with ZisK toolchain
- **Duplicate Prevention**: 30-second window to prevent duplicate submissions
- **Process Management**: Robust process handling and cleanup

### ZisK Integration (Rust)
- **Build Script**: Generates input files with score and game ID
- **ZisK Program**: Rust implementation for proof generation
- **Proof Verification**: Cryptographic verification of generated proofs

## Prerequisites

- Python 3.8+
- Node.js 16+
- Rust toolchain
- ZisK toolchain installed
- Linux/macOS environment

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/amiabix/flappy_bird.git
   cd flappy_bird
   ```

2. **Install Python dependencies**:
   ```bash
   pip install flask flask-cors
   ```

3. **Install Node.js dependencies**:
   ```bash
   cd flappy-bird-game
   npm install
   ```

4. **Install ZisK toolchain**:
   ```bash
   # Follow ZisK installation instructions
   # Ensure cargo-zisk and ziskemu are available
   ```

## Usage

### Starting the System

1. **Start the Backend API**:
   ```bash
   python3 api_server.py
   ```
   The API will be available at `http://localhost:8000`

2. **Start the Frontend**:
   ```bash
   cd flappy-bird-game
   npm run dev -- --host 0.0.0.0
   ```
   The game will be available at `http://localhost:5173`

### Playing the Game

1. **Open the game** in your browser at `http://localhost:5173`
2. **Play Flappy Bird** and achieve a score
3. **Submit your score** to generate a ZisK proof
4. **Monitor proof generation** in real-time
5. **Download the proof** once generation is complete

### API Endpoints

- `POST /api/submit-score` - Submit a game score
- `GET /api/proof-status/<job_id>` - Get proof generation status
- `GET /api/worker-status` - Monitor worker threads
- `GET /api/leaderboard/<difficulty>` - View leaderboard
- `GET /api/download-proof/<job_id>` - Download generated proof
- `GET /api/health` - System health check

## ZisK Proof Generation Process

1. **Input Generation**: `build.rs` creates `input.bin` with score and game ID
2. **Program Build**: `cargo-zisk build --release` compiles the ZisK program
3. **ROM Setup**: `cargo-zisk rom-setup` prepares the execution environment
4. **Program Execution**: `ziskemu` runs the program with input data
5. **Proof Generation**: `cargo-zisk prove` generates the cryptographic proof
6. **Verification**: `cargo-zisk verify` verifies the generated proof

## Configuration

### Environment Variables
- `GAME_SCORE`: The game score to prove
- `GAME_ID`: Unique identifier for the game session

### Script Configuration
- `generate_zk_proof_fixed.sh`: Main ZisK orchestration script
- Timeout settings: 30 minutes for proof generation
- Resource management: Automatic cleanup of ZisK processes

## Security Features

- **Game ID Binding**: Each proof is cryptographically bound to a unique game session
- **Duplicate Prevention**: 30-second window prevents duplicate score submissions
- **Process Isolation**: ZisK processes run in isolated process groups
- **Resource Cleanup**: Automatic cleanup of shared memory and processes

## Monitoring and Debugging

### Real-Time Status
- Live proof generation progress
- Worker thread status monitoring
- Process resource usage tracking
- Error logging and debugging information

### Log Files
- API server logs with detailed request information
- ZisK script execution logs
- Worker thread activity logs
- Error and warning messages

## Troubleshooting

### Common Issues

1. **ZisK Toolchain Errors**:
   - Ensure ZisK is properly installed
   - Check system resource availability
   - Verify Rust toolchain installation

2. **Process Conflicts**:
   - Kill existing ZisK processes: `pkill -f "cargo-zisk"`
   - Clean shared memory: `find /dev/shm -name "ZISK_*" -delete`
   - Restart the API server

3. **Port Conflicts**:
   - Check if ports 8000 (API) and 5173 (Frontend) are available
   - Kill conflicting processes if necessary

### Debug Mode
- Set `debug=False` in `api_server.py` for production stability
- Enable detailed logging for troubleshooting
- Monitor worker thread health and restart if needed

## Performance

- **Proof Generation Time**: 2-15 minutes depending on score complexity
- **Concurrent Processing**: Multiple proof jobs can be queued
- **Resource Usage**: High memory usage during proof generation (8-20 GB)
- **Scalability**: Worker thread system allows horizontal scaling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- ZisK team for the zero-knowledge proof toolchain
- React and Flask communities for the web frameworks
- Rust community for the systems programming language

## Support

For issues and questions:
- Check the troubleshooting section
- Review the logs for error details
- Ensure all prerequisites are met
- Verify ZisK toolchain installation
