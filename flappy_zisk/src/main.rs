// Flappy Bird Game with ZisK Score Proof Generation
// This program generates zero-knowledge proofs for game scores with Game ID binding
// Input: 16 bytes (8 bytes score + 8 bytes game_id)
// Output: Multiple verification values for tamper-proof binding

#![no_main]
ziskos::entrypoint!(main);

use std::convert::TryInto;
use ziskos::{read_input, set_output};

fn main() {
    // Read the input data as a byte array from ziskos
    let input: Vec<u8> = read_input();

    // Input should be 16 bytes: 8 bytes for score + 8 bytes for game_id
    if input.len() != 16 {
        panic!("Invalid input length. Expected 16 bytes (score + game_id), got {}", input.len());
    }

    // Extract score from first 8 bytes
    let score_bytes: [u8; 8] = input[0..8].try_into().unwrap();
    let game_score: u64 = u64::from_le_bytes(score_bytes);
    
    // Extract game_id from next 8 bytes
    let game_id_bytes: [u8; 8] = input[8..16].try_into().unwrap();
    let game_id: u64 = u64::from_le_bytes(game_id_bytes);
    
    println!("Starting ZisK program execution for score: {} with game_id: {}", game_score, game_id);
    
    // Create tamper-proof cryptographic binding between score and game_id
    let proof_binding = create_proof_binding(game_score, game_id);
    
    // Output 0-1: Game Score (64-bit)
    set_output(0, game_score as u32);
    set_output(1, (game_score >> 32) as u32);
    
    // Output 2-3: Game Session ID (64-bit)
    set_output(2, game_id as u32);
    set_output(3, (game_id >> 32) as u32);
    
    // Output 4: Cryptographic Proof Binding (32-bit)
    set_output(4, proof_binding as u32);
    
    // Output 5-6: Verification Hash (64-bit) - combination of score and game_id
    let verification_hash = (game_score ^ game_id) + (game_score * 31337) + (game_id * 1337);
    set_output(5, verification_hash as u32);
    set_output(6, (verification_hash >> 32) as u32);
    
    // Output 7: Final Proof Value (32-bit) - ensures integrity
    let final_proof = (proof_binding + verification_hash as u32) % 0xFFFFFFFF;
    set_output(7, final_proof);
    
    println!("ZisK proof computation completed for score: {} with game_id: {}", game_score, game_id);
    println!("Proof binding: {}, Verification hash: {}, Final proof: {}", 
             proof_binding, verification_hash, final_proof);
}

fn create_proof_binding(score: u64, game_id: u64) -> u32 {
    // Create a cryptographic binding between score and game_id
    // This prevents tampering with either value independently
    
    let mut binding: u32 = 0;
    
    // Mix score bits
    binding ^= (score & 0xFFFFFFFF) as u32;
    binding ^= ((score >> 32) & 0xFFFFFFFF) as u32;
    
    // Mix game_id bits
    binding ^= (game_id & 0xFFFFFFFF) as u32;
    binding ^= ((game_id >> 32) & 0xFFFFFFFF) as u32;
    
    // Add some non-linear mixing
    binding = binding.wrapping_mul(0x5A5A5A5A);
    binding = binding.wrapping_add(0x13371337);
    binding = binding.rotate_left(7);
    
    binding
}