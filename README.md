# Flappy Bird with ZisKVM

A full version of the classic Flappy Bird game, combined with a proof system that verifies scores using the ZisK toolchain. The idea is simple: whenever you finish a game, your score gets locked and verified so no one can fake or tamper with it.

<img width="1024" height="748" alt="image" src="https://github.com/user-attachments/assets/d8c1d32a-6956-4a37-9942-e1fc29aa0e46" />

---

## Overview

This project brings together three main parts:

* A **Flappy Bird game** built with React
* A **Flask backend** to handle score submissions and run verification
* A **ZisK program** (written in Rust) that generates proofs showing each score is real and tied to a unique game session

Every submitted score is verified and linked to the game it came from, making it secure and tamper-proof.

---

## Features

* **Classic Gameplay**: Flappy Bird, rebuilt with React + TypeScript
* **Score Verification**: Every score comes with a cryptographic proof
* **Session Binding**: Proofs are tied to unique game sessions
* **Robust Backend**: Handles multiple jobs and prevents duplicates
* **Real-Time Tracking**: See the status of your proof as it’s generated
  
---

## Architecture

### Frontend (React + TypeScript)

* Game engine with proper physics
* Submit scores securely with duplicate prevention
* Display live updates on proof status
* Modern, responsive interface

### Backend (Flask + Python)

* REST API for score submission and monitoring
* Multi-threaded worker system for proof generation
* 30-second window to prevent duplicate score submissions
* Handles cleanup and resource management

### ZisK Integration (Rust)

* Input builder: packages score + game ID
* Proof program: generates the cryptographic proof
* Verification: checks if the proof is valid

---

## Prerequisites

* Python 3.8+
* Node.js 16+
* Rust toolchain
* ZisK installed (`cargo-zisk` and `ziskemu` available)
* Linux/macOS

---

## Installation

1. Clone the repo:

   ```bash
   git clone https://github.com/amiabix/flappy_bird.git
   cd flappy_bird
   ```

2. Install Python dependencies:

   ```bash
   pip install flask flask-cors
   ```

3. Install Node.js dependencies:

   ```bash
   cd flappy-bird-game
   npm install
   ```

4. Install ZisK toolchain (follow official docs).

---

## Usage

### Start everything

* Run the backend:

  ```bash
  python3 api_server.py
  ```

  → API available at `http://localhost:8000`

* Run the frontend:

  ```bash
  cd flappy-bird-game
  npm run dev -- --host 0.0.0.0
  ```

  → Game available at `http://localhost:5173`

### Play & Verify

1. Open `http://localhost:5173`
2. Play Flappy Bird and set a score
3. Submit score → backend starts proof generation
4. Watch proof status live
5. Download proof when complete

---

## API Endpoints

* `POST /api/submit-score` – Submit a score
* `GET /api/proof-status/<job_id>` – Proof generation status
* `GET /api/worker-status` – Check worker health
* `GET /api/leaderboard/<difficulty>` – Leaderboard
* `GET /api/download-proof/<job_id>` – Download proof
* `GET /api/health` – System check

---

## Proof Generation Steps

1. Input file created with score + game ID
2. Program built with `cargo-zisk build --release`
3. Execution environment prepared (`cargo-zisk rom-setup`)
4. Program runs with `ziskemu`
5. Proof generated (`cargo-zisk prove`)
6. Proof verified (`cargo-zisk verify`)

