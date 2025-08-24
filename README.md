# Flappy Bird ZisK Proof Generation System

A proof generation system for Flappy Bird game scores using ZisK. This project generates proofs for game score's that can be verified without revealing the original game data.

<img width="1003" height="572" alt="image" src="https://github.com/user-attachments/assets/e20d6427-3b92-4b17-a8c0-35e5014bc88b" />


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
4. **Proof Creation**: Generate mathematical proof
5. **Verification**: Verify proof integrity

### 3. System Flow
```
Game Score → API Validation → Job Creation → ZisK Processing → Proof Generation → Status Updates
```

## Security Features

### Global Execution Lock
- **Purpose**: Prevents multiple ZisK processes from running simultaneously
- **Implementation**: System blocks new submissions while processing
- **Benefits**: Resource efficiency, prevents conflicts, ensures sequential processing

### Duplicate Prevention
- **Time Window**: 30-second deduplication window
- **Scope**: Player ID + Score + Difficulty combination
- **Result**: Prevents spam and resource waste

### Input Validation
- **Score Range**: 1-1000 points
- **Data Integrity**: Tamper-proof game ID generation
- **Memory Safety**: Bounds checking and validation

## Monitoring & Status

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
# Change base_port=23200 to avoid conflicts
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

## Performance

### Proof Generation Times
- **Small Scores (1-10)**: 2-5 minutes
- **Medium Scores (11-50)**: 5-10 minutes
- **Large Scores (51-100)**: 10-15 minutes
- **Maximum Score (1000)**: 15-20 minutes

### System Capacity
- **Concurrent Jobs**: 1 (sequential processing)
- **Worker Threads**: 2 (for job management)
- **Memory Usage**: ~500MB per ZisK process
- **Storage**: ~300KB per proof file

## Configuration

### Environment Variables
```bash
# ZisK configuration
export ZISK_BASE_PORT=23200
export ZISK_TIMEOUT=1800

# API configuration
export FLASK_ENV=development
export FLASK_DEBUG=1
```

### Customization Options
- **Timeouts**: Adjust timeout values in API server
- **Worker Count**: Change worker thread count
- **Deduplication Window**: Modify `DEDUP_WINDOW_SECONDS`

## API Reference

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **ZisK Team**: For the Zero-Knowledge System Kit
- **Flappy Bird**: Original game concept
- **React Community**: Frontend framework
- **Flask Community**: Backend framework

## Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Documentation**: [Wiki](https://github.com/your-repo/wiki)

---

**Happy Gaming and Proof Generation!**

