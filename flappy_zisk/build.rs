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

    // Get game ID from environment or generate a default one
    let game_id: u64 = env::var("GAME_ID")
        .unwrap_or_else(|_| {
            // Generate a default game ID based on current timestamp
            let timestamp = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs();
            timestamp.to_string()
        })
        .trim()
        .parse()
        .unwrap_or_else(|_| {
            // Fallback to a simple hash if parsing fails
            game_score.wrapping_mul(0x517cc1b727220a95)
        });

    println!("Building input.bin: score={}, game_id={}", game_score, game_id);

    // Create build directory and write input file
    fs::create_dir_all("build")?;
    let mut file = File::create("build/input.bin")?;
    
    // Write 16 bytes: score + game_id
    file.write_all(&game_score.to_le_bytes())?;
    file.write_all(&game_id.to_le_bytes())?;
    
    println!("Created input.bin: 16 bytes");
    Ok(())
}