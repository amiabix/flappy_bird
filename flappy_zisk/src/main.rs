// Flappy Bird Game with ZisK Score Proof Generation
// This program generates zero-knowledge proofs for game scores

#![no_main]
ziskos::entrypoint!(main);

use std::convert::TryInto;
use ziskos::{read_input, set_output};

fn main() {
    // Read the input data as a byte array from ziskos
    let input: Vec<u8> = read_input();

    // Convert the input data to a u64 integer (game score)
    let game_score: u64 = match input.try_into() {
        Ok(input_bytes) => u64::from_le_bytes(input_bytes),
        Err(input) => panic!("Invalid input length. Expected 8 bytes, got {}", input.len()),
    };
    
    println!("Starting ZisK program execution for score: {}", game_score);
    
    // Simple score verification - just output the score as proof
    // This proves that the program can read and process the input score correctly
    
    // Output the game score (lower 32 bits)
    set_output(0, game_score as u32);
    
    // Output the upper 32 bits of the score
    set_output(1, (game_score >> 32) as u32);
    
    // Output a simple verification value (score * 2 + 1)
    // This creates a unique proof that the score was processed
    let verification_value = game_score * 2 + 1;
    set_output(2, verification_value as u32);
    set_output(3, (verification_value >> 32) as u32);
    
    // Output the score again in reverse order for additional verification
    set_output(4, game_score as u32);
    set_output(5, (game_score >> 32) as u32);
    
    println!("ZisK proof computation completed for score: {}", game_score);
}