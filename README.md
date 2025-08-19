# Flappy Bird with ZisK Proofs

A Flappy Bird game that generates verifiable zero-knowledge proofs of player scores using the ZisK framework.

## Features

- **Classic Flappy Bird Gameplay** - React-based game with smooth controls
- **Real ZisK Proof Generation** - Cryptographic proofs of game scores
- **Live Proof Verification** - See ZisK proofs generated in real-time
- **Score Leaderboard** - Track high scores with verifiable proofs
- **Full Stack Implementation** - Rust backend, Python API, React frontend

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Game    │───▶│  Python API     │───▶│  Rust ZisK      │
│   Frontend      │    │   Server        │    │   Backend       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites

- Rust (latest stable)
- Python 3.8+
- Node.js 16+
- ZisK CLI (`cargo install zisk-cli`)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/amiabix/flappy_bird.git
   cd flappy_bird
   ```

2. **Build the Rust ZisK program**
   ```bash
   cargo-zisk build --release
   ```

3. **Start the Python API server**
   ```bash
   python3 api_server.py
   ```

4. **Start the React frontend**
   ```bash
   cd flappy-bird-game
   npm install
   npm start
   ```

5. **Play the game!** Open http://localhost:3000 in your browser

## How It Works

### 1. Game Play
- Player plays Flappy Bird normally
- When game over occurs, score is captured

### 2. Score Submission
- Frontend sends score to Python API
- API triggers ZisK proof generation

### 3. ZisK Proof Generation
- `build.rs` creates `input.bin` with score data
- `cargo-zisk build --release` builds the ZisK program
- ZisK program reads input and generates cryptographic proof

### 4. Proof Verification
- Real ZisK output displayed in frontend
- Score can be verified independently using `ziskemu`

## Development

### Testing ZisK Proofs

Test the ZisK program directly:
```bash
# Generate input file
cargo run --bin input_generator "player123" 42 5

# Run with ziskemu
ziskemu -e target/riscv64ima-zisk-zkvm-elf/release/flappy_bird_zisk -i build/input.bin
```

### API Testing

Test the API endpoints:
```bash
# Submit a score
curl -X POST http://localhost:8000/api/submit-score \
  -H "Content-Type: application/json" \
  -d '{"player_id": "test", "score": 25, "difficulty": 3}'

# Get leaderboard
curl http://localhost:8000/api/leaderboard
```

## Project Structure

```
flappy_bird/
├── src/
│   ├── main.rs              # ZisK proof generation logic
│   └── game_integration.js  # Frontend-backend integration
├── build.rs                 # Input file generator
├── api_server.py            # Python Flask API server
├── flappy-bird-game/        # React frontend
├── Cargo.toml               # Rust dependencies
└── README.md                # This file
```

## ZisK Integration

This project demonstrates:
- **Real ZisK builds** using `cargo-zisk build --release`
- **Input file generation** for ZisK programs
- **Cryptographic proof generation** of game scores
- **Independent verification** using `ziskemu`

## Future Enhancements

- [ ] Multiplayer support with shared proofs
- [ ] Blockchain integration for score verification
- [ ] Advanced ZisK circuit optimizations
- [ ] Mobile app version
- [ ] Tournament mode with proof verification

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `cargo-zisk build --release`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- ZisK team for the zero-knowledge proof framework
- React team for the frontend framework
- Rust community for the excellent language and tooling

---

**Play Flappy Bird, Generate ZisK Proofs, Verify Everything!**
