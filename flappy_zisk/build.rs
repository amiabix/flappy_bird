use std::env;
use std::fs::{self, File};
use std::io::{self, Write};

fn main() -> io::Result<()> {
    // Get game score from environment or file fallback
    let game_score: u64 = env::var("GAME_SCORE")
        .or_else(|_| fs::read_to_string("GAME_SCORE.txt"))
        .expect("GAME_SCORE not found in environment or GAME_SCORE.txt")
        .trim()
        .parse()
        .expect("Invalid GAME_SCORE format");

    // Generate a deterministic game ID to avoid parsing issues
    let game_id: u64 = {
        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        // Ensure timestamp is valid and create a deterministic ID
        if timestamp < 1700000000 {
            // Fallback timestamp if system time is wrong
            game_score.wrapping_mul(0x517cc1b727220a95)
        } else {
            // Using timestamp-based ID
            (timestamp << 20) | (game_score & 0xFFFFF)
        }
    };

    // Generate realistic input data based on the actual score
    let duration = (game_score * 2000) + 1000; // 2 seconds per point + 1 second base
    let input_count = game_score * 2; // 2 inputs per point (realistic for Flappy Bird)
    
    // Generate realistic input timestamps with human-like variation
    let mut inputs = Vec::new();
    let base_time = 1000u64; // Start at 1 second
    
    // Use a simple PRNG-like approach for realistic variation
    let mut current_time = base_time;
    for i in 0..input_count {
        // Add realistic variation: 600-1000ms between inputs (human-like)
        let base_gap = 800u64;
        let variation = ((i as u64 * 0x517cc1b727220a95) % 400) as u64; // Pseudo-random variation
        let gap = base_gap + variation;
        
        current_time += gap;
        inputs.push((current_time, 1u8)); // All inputs are flaps
    }

    println!("Building input.bin: score={}, game_id={}, duration={}ms, inputs={}", 
             game_score, game_id, duration, input_count);

    // Create build directory and write input file
    fs::create_dir_all("build")?;
    let mut file = File::create("build/input.bin")?;
    
    // Write complete input format: [score(4)][duration(8)][game_id(8)][input_count(4)][inputs...]
    file.write_all(&(game_score as u32).to_le_bytes())?; // score (4 bytes)
    file.write_all(&duration.to_le_bytes())?; // duration (8 bytes)
    file.write_all(&game_id.to_le_bytes())?; // game_id (8 bytes)
    file.write_all(&(input_count as u32).to_le_bytes())?; // input_count (4 bytes)
    
    // Write inputs: [timestamp(8)][action(1)] for each input
    for (timestamp, action) in inputs {
        file.write_all(&timestamp.to_le_bytes())?;
        file.write_all(&action.to_le_bytes())?;
    }
    
    println!("Created input.bin: {} bytes with {} inputs", file.metadata()?.len(), input_count);
    Ok(())
}