use std::env;
use std::fs::{self, File};
use std::io::{self, Write};
use std::path::Path;

// Define constants for the directory and input file name
const OUTPUT_DIR: &str = "build/";
const FILE_NAME: &str = "input.bin";

fn main() -> io::Result<()> {
    // Check if GAME_SCORE is set, if not, create a placeholder file
    let game_score = match env::var("GAME_SCORE") {
        Ok(score_str) => {
            match score_str.parse::<u64>() {
                Ok(score) => {
                    println!("Generating input.bin with game score: {}", score);
                    score
                },
                Err(_) => {
                    println!("Invalid GAME_SCORE format, using placeholder");
                    0
                }
            }
        },
        Err(_) => {
            println!("GAME_SCORE not set, creating placeholder input.bin");
            0
        }
    };

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
