use std::fs::{self, File};
use std::io::{self, Write};
use std::path::Path;
use std::env;

// Define constants for the directory and input file name
const OUTPUT_DIR: &str = "build/";
const FILE_NAME: &str = "input.bin";

fn main() -> io::Result<()> {
    println!("🔧 Flappy Bird ZisK Input Generator");
    println!("=====================================");
    
    // Get command line arguments for score data
    let args: Vec<String> = env::args().collect();
    
    if args.len() != 4 {
        println!("❌ Usage: cargo run --bin build <player_id> <score> <difficulty>");
        println!("   Example: cargo run --bin build player_123 15 3");
        return Ok(());
    }
    
    let player_id = &args[1];
    let score: u32 = args[2].parse().unwrap_or(0);
    let difficulty: u8 = args[3].parse().unwrap_or(1);
    
    println!("📊 Generating input for:");
    println!("   Player ID: {}", player_id);
    println!("   Score: {}", score);
    println!("   Difficulty: {}", difficulty);
    
    // Ensure the output directory exists
    let output_dir = Path::new(OUTPUT_DIR);
    if !output_dir.exists() {
        println!("📁 Creating output directory: {}", OUTPUT_DIR);
        fs::create_dir_all(output_dir)?; 
    }

    // Create the file and write the score data
    let file_path = output_dir.join(FILE_NAME);
    let mut file = File::create(&file_path)?;
    
    // Write player_id_length (1 byte)
    let player_id_length = player_id.len() as u8;
    file.write_all(&[player_id_length])?;
    
    // Write player_id bytes (variable length)
    file.write_all(player_id.as_bytes())?;
    
    // Write score (4 bytes, little-endian)
    file.write_all(&score.to_le_bytes())?;
    
    // Write difficulty (1 byte)
    file.write_all(&[difficulty])?;
    
    println!("💾 Input file generated: {}", file_path.display());
    println!("📏 File size: {} bytes", file_path.metadata()?.len());
    println!("📊 Input format: [length: {}][player_id: {}][score: {}][difficulty: {}]", 
             player_id_length, player_id, score, difficulty);
    println!("✅ Input generation complete!");
    
    Ok(())
}
