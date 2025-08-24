# Flappy Bird ZisK 

A proof generation system for Flappy Bird game scores using ZisK. This project generates proofs for game score's that can be verified without revealing the original game data.


## What This System Does

This system lets you play Flappy Bird, submit your scores, and automatically generates mathematical proofs that verify your achievements are real. Anyone can verify these proofs without seeing your actual gameplay. 

## Architecture

### System Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   ZisK Engine   │
│   (React)       │◄──►│   (Flask)       │◄──►│   (Proof Gen)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Port Configuration
- **Frontend**: Port 5173 (React + Vite)
- **Backend API**: Port 8000 (Flask)
- **ZisK Engine**: Custom ports (23200-23202) to avoid conflicts

## Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Rust toolchain
- ZisK installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd flappy_bird
```

### 2. Install Dependencies

#### Backend (Python)
```bash
pip install flask flask-cors
```

#### Frontend (React)
```bash
cd flappy-bird-game
npm install
```

#### ZisK (Rust)
```bash
cd flappy_zisk
cargo build --release
```

### 3. Configure ZisK
```bash
# Install ZisK tools
cargo install cargo-zisk
cargo install ziskemu

# Verify installation
cargo-zisk --version
ziskemu --version
```

## Running the System

### 1. Start the Backend API
```bash
python3 api_server.py
```

**API Endpoints:**
- `GET /api/health` - System health check
- `GET /api/system-status` - Check if system is ready for submissions
- `POST /api/submit-score` - Submit a game score for proof generation
- `GET /api/proof-status/{job_id}` - Check proof generation status
- `GET /api/leaderboard/{difficulty}` - View leaderboard

### 2. Start the Frontend
```bash
cd flappy-bird-game
npm run dev
```
Access the game at: http://localhost:5173

### 3. Generate ZisK Proofs
```bash
# Manual proof generation
./generate_zk_proof_fixed.sh <score>

# Example: Generate proof for score 5
./generate_zk_proof_fixed.sh 5
```

## How It Works

### 1. Score Submission
1. User plays Flappy Bird and achieves a score
2. Frontend submits score to backend API
3. Backend validates score and creates proof generation job
4. System checks if ZisK is available (global execution lock)

### 2. Proof Generation
1. **Input Generation**: Create binary input file with score data
2. **ZisK Compilation**: Compile Flappy Bird game with ZisK
3. **Execution**: Run game in ZisK environment
4. **Proof Creation**: Generate proof
5. **Verification**: Verify proof integrity

### 3. System Flow
```
Game Score → API Validation → Job Creation → ZisK Processing → Proof Generation → Status Updates
```

### System Status Endpoints
```bash
# Check if system is ready for submissions
curl http://localhost:8000/api/system-status

# Health check with detailed status
curl http://localhost:8000/api/health
```

### Status Responses
```json
{
  "ready_for_submissions": true,
  "system_busy": false,
  "message": "System is ready for new score submissions",
  "active_jobs": 0
}
```

### Proof Generation Status
- **PENDING**: Job created, waiting for ZisK execution
- **IN_PROGRESS**: ZisK proof generation in progress
- **COMPLETED**: Proof generated successfully
- **FAILED**: Proof generation failed
- **TIMEOUT**: Proof generation timed out

## Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using ZisK ports
netstat -tuln | grep -E "23118|23119|23120"

# Use custom ports in generate_zk_proof_fixed.sh
```

#### System Busy Error
```
Error: "System is currently busy generating ZisK proofs"
Solution: Wait for current proof to complete (5-15 minutes)
```

#### Frontend Stuck on "Submitting score..."
```
Cause: System busy, frontend not handling 503 response
Solution: Refresh page, system will show proper status
```

### Debug Commands
```bash
# Check ZisK processes
ps aux | grep -E "zec-keccakf|cargo-zisk|ziskemu"

# Check API server logs
tail -f api_server.log

# Check system status
curl -s http://localhost:8000/api/system-status | jq
```

### Environment Variables
```bash
# ZisK configuration
export ZISK_BASE_PORT=23200
export ZISK_TIMEOUT=1800

# API configuration
export FLASK_ENV=development
export FLASK_DEBUG=1
```

### Submit Score
```bash
POST /api/submit-score
Content-Type: application/json

{
  "player_id": "player_123",
  "score": 15,
  "difficulty": 1
}
```

### Response Format
```json
{
  "success": true,
  "job_id": "uuid-here",
  "message": "Score submitted successfully",
  "proof_status": "pending"
}
```

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Testing
```bash
# Test backend API
python3 -m pytest tests/

# Test frontend
cd flappy-bird-game
npm test

# Test ZisK integration
./generate_zk_proof_fixed.sh 5
```
---

**Happy Gaming and Proof Generation with ZisK!**

