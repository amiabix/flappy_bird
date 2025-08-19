// Flappy Bird Game with ZisK Score Proof Generation
// This program generates zero-knowledge proofs for game scores

#![no_main]
ziskos::entrypoint!(main);



use sha2::{Digest, Sha256};
use std::convert::TryInto;
use ziskos::{read_input, set_output};
use byteorder::ByteOrder;
use serde::{Deserialize, Serialize};
// Removed chrono and uuid dependencies


#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GameScore {
    pub player_id: String,
    pub score: u32,
    pub timestamp: u64,  // Unix timestamp instead of DateTime
    pub game_session_id: String,
    pub difficulty_level: u8,
    pub proof_hash: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct ScoreProof {
    pub score_data: GameScore,
    pub merkle_root: String,
    pub proof_path: Vec<String>,
    pub public_inputs: Vec<u8>,
}

impl GameScore {
    pub fn new(player_id: String, score: u32, difficulty_level: u8) -> Self {
        // Use a fixed timestamp for ZisK compatibility
        let timestamp = 1234567890u64; // Fixed timestamp
        let game_session_id = format!("session_{}", score);
        
        Self {
            player_id,
            score,
            timestamp,
            game_session_id,
            difficulty_level,
            proof_hash: String::new(), // Will be computed later
        }
    }

    pub fn compute_proof_hash(&mut self) {
        let score_data = format!(
            "{}:{}:{}:{}:{}",
            self.player_id,
            self.score,
            self.timestamp,
            self.game_session_id,
            self.difficulty_level
        );
        
        let mut hasher = Sha256::new();
        hasher.update(score_data.as_bytes());
        let digest = hasher.finalize();
        self.proof_hash = format!("{:x}", digest);
    }
}

impl ScoreProof {
    pub fn new(score: GameScore) -> Self {
        let mut score_with_hash = score.clone();
        score_with_hash.compute_proof_hash();
        
        // Generate a simple merkle tree proof (in production, use a proper merkle tree)
        let merkle_root = Self::generate_merkle_root(&score_with_hash);
        let proof_path = Self::generate_proof_path(&score_with_hash);
        let public_inputs = Self::serialize_public_inputs(&score_with_hash);
        
        Self {
            score_data: score_with_hash,
            merkle_root,
            proof_path,
            public_inputs,
        }
    }

    fn generate_merkle_root(score: &GameScore) -> String {
        let mut hasher = Sha256::new();
        hasher.update(score.proof_hash.as_bytes());
        hasher.update(score.timestamp.to_le_bytes().as_ref());
        let digest = hasher.finalize();
        format!("{:x}", digest)
    }

    fn generate_proof_path(score: &GameScore) -> Vec<String> {
        // Generate a proof path for the score
        let mut path = Vec::new();
        
        // Add score hash
        path.push(score.proof_hash.clone());
        
        // Add timestamp hash
        let mut hasher = Sha256::new();
        hasher.update(score.timestamp.to_le_bytes().as_ref());
        let digest = hasher.finalize();
        path.push(format!("{:x}", digest));
        
        // Add difficulty hash
        let mut hasher = Sha256::new();
        hasher.update(&[score.difficulty_level]);
        let digest = hasher.finalize();
        path.push(format!("{:x}", digest));
        
        path
    }

    fn serialize_public_inputs(score: &GameScore) -> Vec<u8> {
        let mut inputs = Vec::new();
        
        // Add score as 4 bytes
        inputs.extend_from_slice(&score.score.to_le_bytes());
        
        // Add difficulty as 1 byte
        inputs.push(score.difficulty_level);
        
        // Add timestamp as 8 bytes
        inputs.extend_from_slice(&score.timestamp.to_le_bytes());
        
        inputs
    }
}

fn main() {
    // Read the input data as a byte array from ziskos
    let input: Vec<u8> = read_input();
    
    // Parse input: [player_id_length: u8][player_id_bytes][score: u32][difficulty: u8]
    if input.len() < 6 {
        panic!("Invalid input length. Expected at least 6 bytes");
    }
    
    let player_id_length = input[0] as usize;
    if input.len() < 1 + player_id_length + 4 + 1 {
        panic!("Invalid input length for player_id");
    }
    
    let player_id = String::from_utf8_lossy(&input[1..1+player_id_length]).to_string();
    let score_start = 1 + player_id_length;
    let score_bytes: [u8; 4] = input[score_start..score_start+4].try_into().unwrap();
    let score = u32::from_le_bytes(score_bytes);
    let difficulty = input[score_start + 4];
    
    // Create game score
    let game_score = GameScore::new(player_id, score, difficulty);
    
    // Generate score proof
    let score_proof = ScoreProof::new(game_score);
    
    // Generate score proof (proof_data is used for ZisK verification)
    
    // Set outputs for ZisK
    // Output 0: Score value
    set_output(0, score_proof.score_data.score as u32);
    
    // Output 1: Difficulty level
    set_output(1, score_proof.score_data.difficulty_level as u32);
    
    // Output 2: Timestamp (lower 32 bits)
    set_output(2, (score_proof.score_data.timestamp & 0xFFFFFFFF) as u32);
    
    // Output 3: Timestamp (upper 32 bits)
    set_output(3, (score_proof.score_data.timestamp >> 32) as u32);
    
    // Output 4-7: Merkle root hash (split into 32-bit chunks)
    let merkle_bytes = hex::decode(&score_proof.merkle_root).unwrap_or_default();
    for i in 0..4 {
        if i * 4 < merkle_bytes.len() {
            let chunk = if i * 4 + 4 <= merkle_bytes.len() {
                &merkle_bytes[i * 4..i * 4 + 4]
            } else {
                &merkle_bytes[i * 4..]
            };
            
            let mut padded = [0u8; 4];
            padded[..chunk.len()].copy_from_slice(chunk);
            let val = byteorder::BigEndian::read_u32(&padded);
            set_output(4 + i, val);
        } else {
            set_output(4 + i, 0);
        }
    }
}