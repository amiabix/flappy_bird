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
            // Try to read from a file as fallback
            match std::fs::read_to_string("GAME_SCORE.txt") {
                Ok(content) => {
                    println!("Reading GAME_SCORE from file: '{}'", content.trim());
                    match content.trim().parse::<u64>() {
                        Ok(score) => {
                            println!("Parsed score from file successfully: {}", score);
                            score
                        },
                        Err(e) => {
                            println!("Invalid GAME_SCORE format in file '{}': {:?}, using placeholder", content.trim(), e);
                            0
                        }
                    }
                },
                Err(_) => {
                    println!("No GAME_SCORE file found, using placeholder");
                    0
                }
            }
        }
    };
    
    // Get Game ID from environment for tamper-proof binding
    let game_id = match env::var("GAME_ID") {
        Ok(id_str) => {
            println!("GAME_ID found in environment: '{}'", id_str);
            match id_str.parse::<u64>() {
                Ok(id) => {
                    println!("Parsed game_id successfully: {}", id);
                    id
                },
                Err(e) => {
                    println!("Invalid GAME_ID format '{}': {:?}, generating default", id_str, e);
                    // Generate a default game ID based on score and timestamp
                    let timestamp = std::time::SystemTime::now()
                        .duration_since(std::time::UNIX_EPOCH)
                        .unwrap()
                        .as_secs();
                    let default_id = (timestamp << 20) | (game_score % 1048576);
                    println!("Generated default game_id: {}", default_id);
                    default_id
                }
            }
        },
        Err(_) => {
            // Generate a default game ID based on score and timestamp
            let timestamp = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs();
            let default_id = (timestamp << 20) | (game_score % 1048576);
            println!("GAME_ID not found, generated default game_id: {}", default_id);
            default_id
        }
    };
    
    println!("Final game_score value: {}", game_score);
    println!("Final game_id value: {}", game_id);
    println!("=== build.rs DEBUG END ===");

    // Ensure the output directory exists
    let output_dir = Path::new(OUTPUT_DIR);
    if !output_dir.exists() {
        // Create the directory and any necessary parent directories
        fs::create_dir_all(output_dir)?; 
    }

    // Create the file and write both score and game_id in little-endian format
    let file_path = output_dir.join(FILE_NAME);
    let mut file = File::create(&file_path)?;
    
    // Write score (8 bytes) - first 8 bytes
    file.write_all(&game_score.to_le_bytes())?;
    // Write game_id (8 bytes) - next 8 bytes
    file.write_all(&game_id.to_le_bytes())?;
    
    if game_score > 0 {
        println!("Input file generated successfully at: {:?}", file_path);
        println!("File size: {} bytes (score: {} + game_id: {})", 
                 std::mem::size_of::<u64>() * 2, 
                 std::mem::size_of::<u64>(), 
                 std::mem::size_of::<u64>());
        println!("Content: Score={}, GameID={}", game_score, game_id);
    } else {
        println!("Placeholder input.bin created at: {:?}", file_path);
        println!("File size: {} bytes (score: {} + game_id: {})", 
                 std::mem::size_of::<u64>() * 2, 
                 std::mem::size_of::<u64>(), 
                 std::mem::size_of::<u64>());
    }

    Ok(())
}
