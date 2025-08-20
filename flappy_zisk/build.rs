use std::env;
use std::fs::{self, File};
use std::io::{self, Write};
use std::path::Path;

// Define constants for the directory and input file name
const OUTPUT_DIR: &str = "build/";
const FILE_NAME: &str = "input.bin";

fn main() -> io::Result<()> {
    println!("=== build.rs DEBUG START ===");
    println!("Current working directory: {:?}", env::current_dir()?);
    println!("All environment variables:");
    for (key, value) in env::vars() {
        if key.contains("GAME") || key.contains("SCORE") {
            println!("  {} = {}", key, value);
        }
    }
    
    // Check if GAME_SCORE is set, if not, create a placeholder file
    let game_score = match env::var("GAME_SCORE") {
        Ok(score_str) => {
            println!("GAME_SCORE found in environment: '{}'", score_str);
            match score_str.parse::<u64>() {
                Ok(score) => {
                    println!("Parsed score successfully: {}", score);
                    score
                },
                Err(e) => {
                    println!("Invalid GAME_SCORE format '{}': {:?}, using placeholder", score_str, e);
                    0
                }
            }
        },
        Err(e) => {
            println!("GAME_SCORE not found in environment: {:?}, creating placeholder input.bin", e);
            0
        }
    };
    
    println!("Final game_score value: {}", game_score);
    println!("=== build.rs DEBUG END ===");

    // Ensure the output directory exists
    let output_dir = Path::new(OUTPUT_DIR);
    if !output_dir.exists() {
        // Create the directory and any necessary parent directories
        fs::create_dir_all(output_dir)?; 
    }

    // Create the file and write the game score in little-endian format
    let file_path = output_dir.join(FILE_NAME);
    let mut file = File::create(&file_path)?;
    file.write_all(&game_score.to_le_bytes())?; 
    
    if game_score > 0 {
        println!("Input file generated successfully at: {:?}", file_path);
        println!("File size: {} bytes", std::mem::size_of::<u64>());
    } else {
        println!("Placeholder input.bin created at: {:?}", file_path);
    }

    Ok(())
}
