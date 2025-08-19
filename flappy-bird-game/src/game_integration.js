/**
 * Flappy Bird Game Integration with Rust ZisK Backend
 * Handles score submission, proof generation, and leaderboard management
 */

class FlappyBirdIntegration {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.playerId = this.generatePlayerId();
        this.currentSessionId = null;
        this.difficultyLevel = 1;
        this.scoreHistory = [];
    }

    /**
     * Generate a unique player ID for this session
     */
    generatePlayerId() {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substr(2, 9);
        return `player_${timestamp}_${random}`;
    }

    /**
     * Start a new game session
     */
    startNewSession() {
        this.currentSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        this.scoreHistory = [];
        console.log(`New game session started: ${this.currentSessionId}`);
        return this.currentSessionId;
    }

    /**
     * Set the difficulty level for the current game
     */
    setDifficulty(level) {
        if (level >= 1 && level <= 10) {
            this.difficultyLevel = level;
            console.log(`Difficulty set to level ${level}`);
        } else {
            console.warn(`Invalid difficulty level: ${level}. Must be between 1-10.`);
        }
    }

    /**
     * Submit a score to the Rust backend for proof generation
     */
    async submitScore(score) {
        if (!this.currentSessionId) {
            this.startNewSession();
        }

        const scoreData = {
            player_id: this.playerId,
            score: score,
            difficulty: this.difficultyLevel,
            game_session_id: this.currentSessionId,
            timestamp: Date.now()
        };

        try {
            // First, try to submit to the Rust backend
            const response = await this.submitToRustBackend(scoreData);
            
            if (response.success) {
                // Store the score locally
                this.scoreHistory.push({
                    ...scoreData,
                    proof: response.proof,
                    leaderboard_position: response.leaderboard_position,
                    submitted_at: new Date().toISOString()
                });

                console.log(`Score ${score} submitted successfully! Position: ${response.leaderboard_position}`);
                
                // Emit event for the game
                this.emitScoreSubmitted(scoreData, response);
                
                return response;
            } else {
                throw new Error(response.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Failed to submit score to Rust backend:', error);
            
            // Fallback: store score locally without proof
            this.scoreHistory.push({
                ...scoreData,
                proof: null,
                leaderboard_position: null,
                submitted_at: new Date().toISOString(),
                error: error.message
            });

            // Emit fallback event
            this.emitScoreSubmitted(scoreData, { success: false, error: error.message });
            
            return { success: false, error: error.message };
        }
    }

    /**
     * Submit score to the Rust ZisK backend
     */
    async submitToRustBackend(scoreData) {
        try {
            console.log('🚀 Submitting to Rust backend via Python API...');
            
            // Call the Python API server
            const response = await fetch(`${this.baseUrl}/api/submit-score`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    player_id: scoreData.player_id,
                    score: scoreData.score,
                    difficulty: scoreData.difficulty
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('✅ Rust backend response:', data);
            
            if (data.success) {
                return {
                    success: true,
                    proof: data.proof,
                    leaderboard_position: data.leaderboard_position || 1,
                    error: null
                };
            } else {
                throw new Error(data.error || 'Unknown error from backend');
            }
            
        } catch (error) {
            console.error('❌ Rust backend submission failed:', error);
            throw error;
        }
    }

    /**
     * Generate a mock proof hash for demonstration
     */
    generateMockProofHash(scoreData) {
        const data = `${scoreData.player_id}:${scoreData.score}:${scoreData.timestamp}:${scoreData.game_session_id}:${scoreData.difficulty}`;
        return btoa(data).replace(/[^a-zA-Z0-9]/g, '').substr(0, 32);
    }

    /**
     * Generate a mock merkle root for demonstration
     */
    generateMerkleRoot(scoreData) {
        const hash = this.generateMockProofHash(scoreData);
        return btoa(hash + scoreData.timestamp.toString()).replace(/[^a-zA-Z0-9]/g, '').substr(0, 32);
    }

    /**
     * Generate a mock proof path for demonstration
     */
    generateMockProofPath(scoreData) {
        return [
            this.generateMockProofHash(scoreData),
            btoa(scoreData.timestamp.toString()).replace(/[^a-zA-Z0-9]/g, '').substr(0, 16),
            btoa(scoreData.difficulty.toString()).replace(/[^a-zA-Z0-9]/g, '').substr(0, 16)
        ];
    }

    /**
     * Serialize public inputs for ZisK
     */
    serializePublicInputs(scoreData) {
        const buffer = new ArrayBuffer(13); // 4 bytes for score + 1 byte for difficulty + 8 bytes for timestamp
        const view = new DataView(buffer);
        
        view.setUint32(0, scoreData.score, true); // Little-endian
        view.setUint8(4, scoreData.difficulty);
        view.setBigUint64(5, BigInt(scoreData.timestamp), true); // Little-endian
        
        return Array.from(new Uint8Array(buffer));
    }

    /**
     * Get the current player's statistics
     */
    getPlayerStats() {
        if (this.scoreHistory.length === 0) {
            return {
                total_games: 0,
                highest_score: 0,
                average_score: 0,
                total_score: 0
            };
        }

        const totalScore = this.scoreHistory.reduce((sum, entry) => sum + entry.score, 0);
        const highestScore = Math.max(...this.scoreHistory.map(entry => entry.score));
        const averageScore = totalScore / this.scoreHistory.length;

        return {
            total_games: this.scoreHistory.length,
            highest_score: highestScore,
            average_score: Math.round(averageScore * 100) / 100,
            total_score: totalScore
        };
    }

    /**
     * Get the player's score history
     */
    getScoreHistory() {
        return [...this.scoreHistory].reverse(); // Most recent first
    }

    /**
     * Verify a score proof (would use ZisK verification in production)
     */
    async verifyScoreProof(proof) {
        try {
            // In production, this would call the ZisK verification endpoint
            const response = await fetch(`${this.baseUrl}/api/verify-proof`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(proof)
            });

            if (response.ok) {
                const result = await response.json();
                return result.verified;
            } else {
                throw new Error('Verification request failed');
            }
        } catch (error) {
            console.error('Proof verification failed:', error);
            return false;
        }
    }

    /**
     * Emit score submitted event
     */
    emitScoreSubmitted(scoreData, response) {
        const event = new CustomEvent('scoreSubmitted', {
            detail: {
                scoreData,
                response,
                timestamp: new Date().toISOString()
            }
        });
        window.dispatchEvent(event);
    }

    /**
     * Get leaderboard data
     */
    async getLeaderboard(difficulty = null, limit = 10) {
        try {
            const url = difficulty 
                ? `${this.baseUrl}/api/leaderboard/${difficulty}?limit=${limit}`
                : `${this.baseUrl}/api/leaderboard?limit=${limit}`;
            
            const response = await fetch(url);
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Failed to fetch leaderboard');
            }
        } catch (error) {
            console.error('Failed to fetch leaderboard:', error);
            return [];
        }
    }

    /**
     * Export player data for backup
     */
    exportPlayerData() {
        const data = {
            player_id: this.playerId,
            export_date: new Date().toISOString(),
            score_history: this.scoreHistory,
            stats: this.getPlayerStats()
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `flappy_bird_scores_${this.playerId}_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
    }

    /**
     * Import player data from backup
     */
    importPlayerData(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                try {
                    const data = JSON.parse(e.target.result);
                    
                    if (data.player_id && data.score_history) {
                        this.playerId = data.player_id;
                        this.scoreHistory = data.score_history;
                        console.log(`Imported ${data.score_history.length} scores for player ${data.player_id}`);
                        resolve(data);
                    } else {
                        reject(new Error('Invalid backup file format'));
                    }
                } catch (error) {
                    reject(new Error('Failed to parse backup file'));
                }
            };
            
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    }
}

// Export for use in React components
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FlappyBirdIntegration;
} else if (typeof window !== 'undefined') {
    window.FlappyBirdIntegration = FlappyBirdIntegration;
}
