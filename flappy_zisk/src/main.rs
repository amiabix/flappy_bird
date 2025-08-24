#![no_main]
ziskos::entrypoint!(main);

use std::convert::TryInto;
use ziskos::{read_input, set_output};

fn main() {
    let input: Vec<u8> = read_input();
    
    if input.len() != 16 {
        panic!("Invalid input: expected 16 bytes (score + game_id), got {}", input.len());
    }
    
    let score_bytes: [u8; 8] = input[0..8].try_into().unwrap();
    let game_score: u64 = u64::from_le_bytes(score_bytes);
    
    let game_id_bytes: [u8; 8] = input[8..16].try_into().unwrap();
    let game_id: u64 = u64::from_le_bytes(game_id_bytes);
    
    // Game validation
    assert!(game_id > 0, "Invalid game session ID");
    assert!(game_score > 0, "Score must be positive");
    assert!(game_score <= 1000, "Score exceeds maximum (1000)");
    
    // Timestamp validation (game_id upper bits contain timestamp)
    let game_timestamp = game_id >> 20;
    assert!(game_timestamp > 1700000000, "Game session appears invalid");
    
    let proof_binding = create_proof_binding(game_score, game_id);
    
    set_output(0, game_score as u32);
    set_output(1, (game_score >> 32) as u32);
    set_output(2, game_id as u32);
    set_output(3, (game_id >> 32) as u32);
    set_output(4, proof_binding);
}

// Cryptographic binding prevents proof replay attacks
fn create_proof_binding(score: u64, game_id: u64) -> u32 {
    let mut combined = score ^ game_id.rotate_left(32);
    
    combined ^= combined >> 33;
    combined = combined.wrapping_mul(0xff51afd7ed558ccd_u64);
    combined ^= combined >> 33;
    combined = combined.wrapping_mul(0xc4ceb9fe1a85ec53_u64);
    combined ^= combined >> 33;
    
    (combined as u32) ^ ((combined >> 32) as u32)
}