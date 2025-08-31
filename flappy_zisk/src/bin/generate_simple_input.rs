use std::fs::File;
use std::io::Write;
use std::env;

fn main() {
    // Get score from command line argument or environment variable
    let score = env::args()
        .nth(1)
        .and_then(|arg| arg.parse::<u32>().ok())
        .or_else(|| env::var("GAME_SCORE").ok().and_then(|s| s.parse::<u32>().ok()))
        .or_else(|| std::fs::read_to_string("GAME_SCORE.txt").ok().and_then(|s| s.trim().parse::<u32>().ok()))
        .expect("Failed to get score from command line, environment, or GAME_SCORE.txt");

    println!("🎯 Generating input for REAL score: {}", score);
    
    // Generate realistic input data based on the actual score
    let duration = (score as u64 * 2000) + 1000; // 2 seconds per point + 1 second base
    let game_id = 12345u64; // Simple game ID
    let input_count = score * 2; // 2 inputs per point (realistic for Flappy Bird)
    
    // Generate realistic input timestamps
    let mut inputs = Vec::new();
    let base_time = 1000u64; // Start at 1 second
    
    for i in 0..input_count {
        let timestamp = base_time + (i as u64 * 800); // 800ms between inputs
        inputs.push((timestamp, 1u8)); // All inputs are flaps
    }

    // Create input.bin with REAL score data
    let mut file = File::create("input.bin").expect("Failed to create input.bin");
    
    // Write score (4 bytes) - THIS IS YOUR REAL SCORE!
    file.write_all(&score.to_le_bytes()).expect("Failed to write score");
    
    // Write duration (8 bytes)
    file.write_all(&duration.to_le_bytes()).expect("Failed to write duration");
    
    // Write game_id (8 bytes)
    file.write_all(&game_id.to_le_bytes()).expect("Failed to write game_id");
    
    // Write input_count (4 bytes)
    file.write_all(&input_count.to_le_bytes()).expect("Failed to write input_count");
    
    // Write inputs
    for (timestamp, action) in inputs {
        file.write_all(&timestamp.to_le_bytes()).expect("Failed to write timestamp");
        file.write_all(&action.to_le_bytes()).expect("Failed to write action");
    }
    
    println!("✅ Input file generated with REAL score {}: input.bin", score);
    println!("📊 Input size: {} bytes", file.metadata().unwrap().len());
    println!("🎮 Duration: {}ms, Inputs: {}", duration, input_count);
}
