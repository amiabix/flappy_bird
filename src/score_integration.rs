// Score Integration Module for Flappy Bird
// Handles score processing and proof generation

use crate::{GameScore, ScoreProof};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Mutex;
use lazy_static::lazy_static;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ScoreSubmission {
    pub player_id: String,
    pub score: u32,
    pub difficulty: u8,
    pub game_session_id: Option<String>,
    pub timestamp: Option<i64>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct ScoreResponse {
    pub success: bool,
    pub proof: Option<ScoreProof>,
    pub error: Option<String>,
    pub leaderboard_position: Option<u32>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct LeaderboardEntry {
    pub player_id: String,
    pub score: u32,
    pub difficulty: u8,
    pub timestamp: i64,
    pub proof_hash: String,
}

lazy_static! {
    static ref SCORE_DATABASE: Mutex<HashMap<String, Vec<LeaderboardEntry>>> = Mutex::new(HashMap::new());
}

impl ScoreSubmission {
    pub fn new(player_id: String, score: u32, difficulty: u8) -> Self {
        Self {
            player_id,
            score,
            difficulty,
            game_session_id: None,
            timestamp: None,
        }
    }

    pub fn with_session(mut self, session_id: String) -> Self {
        self.game_session_id = Some(session_id);
        self
    }

    pub fn with_timestamp(mut self, timestamp: i64) -> Self {
        self.timestamp = Some(timestamp);
        self
    }

    pub fn validate(&self) -> Result<(), String> {
        if self.player_id.trim().is_empty() {
            return Err("Player ID cannot be empty".to_string());
        }
        
        if self.score > 1_000_000 {
            return Err("Score seems unreasonably high".to_string());
        }
        
        if self.difficulty > 10 {
            return Err("Invalid difficulty level".to_string());
        }
        
        Ok(())
    }
}

pub struct ScoreManager;

impl ScoreManager {
    /// Process a score submission and generate a proof
    pub fn process_score(submission: ScoreSubmission) -> Result<ScoreResponse, String> {
        // Validate submission
        submission.validate()?;
        
        // Create game score
        let game_score = GameScore::new(
            submission.player_id.clone(),
            submission.score,
            submission.difficulty,
        );
        
        // Generate proof
        let score_proof = ScoreProof::new(game_score.clone());
        
        // Store in leaderboard
        let leaderboard_position = Self::add_to_leaderboard(&game_score)?;
        
        Ok(ScoreResponse {
            success: true,
            proof: Some(score_proof),
            error: None,
            leaderboard_position: Some(leaderboard_position),
        })
    }
    
    /// Add score to leaderboard and return position
    fn add_to_leaderboard(score: &GameScore) -> Result<u32, String> {
        let mut db = SCORE_DATABASE.lock().map_err(|_| "Database lock error")?;
        
        let difficulty_key = score.difficulty_level.to_string();
        let entries = db.entry(difficulty_key).or_insert_with(Vec::new);
        
        let entry = LeaderboardEntry {
            player_id: score.player_id.clone(),
            score: score.score,
            difficulty: score.difficulty_level,
            timestamp: score.timestamp.timestamp(),
            proof_hash: score.proof_hash.clone(),
        };
        
        entries.push(entry);
        
        // Sort by score (descending) and timestamp (ascending for ties)
        entries.sort_by(|a, b| {
            b.score.cmp(&a.score)
                .then(a.timestamp.cmp(&b.timestamp))
        });
        
        // Find position (1-indexed)
        let position = entries.iter()
            .position(|e| e.proof_hash == score.proof_hash)
            .map(|p| p as u32 + 1)
            .unwrap_or(1);
        
        Ok(position)
    }
    
    /// Get leaderboard for a specific difficulty
    pub fn get_leaderboard(difficulty: u8, limit: usize) -> Result<Vec<LeaderboardEntry>, String> {
        let db = SCORE_DATABASE.lock().map_err(|_| "Database lock error")?;
        
        let difficulty_key = difficulty.to_string();
        let entries = db.get(&difficulty_key).cloned().unwrap_or_default();
        
        Ok(entries.into_iter().take(limit).collect())
    }
    
    /// Get top scores across all difficulties
    pub fn get_global_leaderboard(limit: usize) -> Result<Vec<LeaderboardEntry>, String> {
        let db = SCORE_DATABASE.lock().map_err(|_| "Database lock error")?;
        
        let mut all_entries = Vec::new();
        
        for entries in db.values() {
            all_entries.extend(entries.clone());
        }
        
        // Sort by score (descending) and timestamp (ascending for ties)
        all_entries.sort_by(|a, b| {
            b.score.cmp(&a.score)
                .then(a.timestamp.cmp(&b.timestamp))
        });
        
        Ok(all_entries.into_iter().take(limit).collect())
    }
    
    /// Verify a score proof
    pub fn verify_proof(proof: &ScoreProof) -> Result<bool, String> {
        // Basic verification - in production, use proper ZisK verification
        let expected_hash = proof.score_data.proof_hash.clone();
        let mut score_copy = proof.score_data.clone();
        score_copy.compute_proof_hash();
        
        Ok(expected_hash == score_copy.proof_hash)
    }
    
    /// Get player statistics
    pub fn get_player_stats(player_id: &str) -> Result<PlayerStats, String> {
        let db = SCORE_DATABASE.lock().map_err(|_| "Database lock error")?;
        
        let mut stats = PlayerStats {
            player_id: player_id.to_string(),
            total_games: 0,
            highest_score: 0,
            average_score: 0.0,
            difficulty_breakdown: HashMap::new(),
        };
        
        let mut total_score = 0u64;
        
        for (difficulty_str, entries) in db.iter() {
            let difficulty = difficulty_str.parse::<u8>().unwrap_or(0);
            let player_entries: Vec<_> = entries.iter()
                .filter(|e| e.player_id == player_id)
                .collect();
            
            if !player_entries.is_empty() {
                let difficulty_stats = DifficultyStats {
                    games_played: player_entries.len() as u32,
                    highest_score: player_entries.iter().map(|e| e.score).max().unwrap_or(0),
                    average_score: player_entries.iter().map(|e| e.score as u64).sum::<u64>() as f64 / player_entries.len() as f64,
                };
                
                stats.difficulty_breakdown.insert(difficulty, difficulty_stats);
                stats.total_games += player_entries.len() as u32;
                
                for entry in player_entries {
                    total_score += entry.score as u64;
                    if entry.score > stats.highest_score {
                        stats.highest_score = entry.score;
                    }
                }
            }
        }
        
        if stats.total_games > 0 {
            stats.average_score = total_score as f64 / stats.total_games as f64;
        }
        
        Ok(stats)
    }
}

#[derive(Serialize, Deserialize, Debug)]
pub struct PlayerStats {
    pub player_id: String,
    pub total_games: u32,
    pub highest_score: u32,
    pub average_score: f64,
    pub difficulty_breakdown: HashMap<u8, DifficultyStats>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct DifficultyStats {
    pub games_played: u32,
    pub highest_score: u32,
    pub average_score: f64,
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_score_submission_validation() {
        let valid = ScoreSubmission::new("Alice".to_string(), 100, 1);
        assert!(valid.validate().is_ok());
        
        let invalid_id = ScoreSubmission::new("".to_string(), 100, 1);
        assert!(invalid_id.validate().is_err());
        
        let invalid_score = ScoreSubmission::new("Alice".to_string(), 2_000_000, 1);
        assert!(invalid_score.validate().is_err());
        
        let invalid_difficulty = ScoreSubmission::new("Alice".to_string(), 100, 15);
        assert!(invalid_difficulty.validate().is_err());
    }
    
    #[test]
    fn test_score_processing() {
        let submission = ScoreSubmission::new("Bob".to_string(), 250, 2);
        let result = ScoreManager::process_score(submission);
        
        assert!(result.is_ok());
        let response = result.unwrap();
        assert!(response.success);
        assert!(response.proof.is_some());
        assert!(response.leaderboard_position.is_some());
    }
}
