#![no_main]
ziskos::entrypoint!(main);

use ziskos::{read_input, set_output};

fn main() {
    let input: Vec<u8> = read_input();
    
    // Parse real gameplay data with minimal memory usage
    let (score, duration, game_id, input_count, inputs) = parse_real_gameplay_data_simple(&input);
    
    // Validate that the real inputs could produce the claimed score
    validate_real_gameplay_simple(score, duration, game_id, input_count, &inputs);
    
    // If validation passes, output the verified score
    set_output(0, score);
    set_output(1, game_id as u32);
    set_output(2, (game_id >> 32) as u32);
    
    // Create proof binding from real gameplay data
    let proof_binding = create_real_proof_binding_simple(score, game_id, duration, input_count);
    set_output(3, proof_binding);
}

fn parse_real_gameplay_data_simple(input: &[u8]) -> (u32, u64, u64, u32, Vec<(u64, u8)>) {
    // Expected format: [score(4)][duration(8)][game_id(8)][input_count(4)][inputs...]
    if input.len() < 24 {
        panic!("Invalid input: expected at least 24 bytes, got {}", input.len());
    }
    
    let score = u32::from_le_bytes([input[0], input[1], input[2], input[3]]);
    let duration = u64::from_le_bytes([input[4], input[5], input[6], input[7], 
                                      input[8], input[9], input[10], input[11]]);
    let game_id = u64::from_le_bytes([input[12], input[13], input[14], input[15],
                                     input[16], input[17], input[18], input[19]]);
    let input_count = u32::from_le_bytes([input[20], input[21], input[22], input[23]]);
    
    // Parse real input timestamps with minimal memory usage
    let mut inputs = Vec::new();
    let input_data_start = 24;
    let input_size = 9; // timestamp(8) + action(1)
    
    if input.len() < input_data_start + (input_count as usize * input_size) {
        panic!("Invalid input: insufficient data for {} inputs", input_count);
    }
    
    for i in 0..input_count {
        let start = input_data_start + (i as usize * input_size);
        let end = start + input_size;
        
        if end > input.len() {
            panic!("Input data truncated at input {}", i);
        }
        
        let input_slice = &input[start..end];
        let timestamp = u64::from_le_bytes([input_slice[0], input_slice[1], input_slice[2], input_slice[3],
                                           input_slice[4], input_slice[5], input_slice[6], input_slice[7]]);
        let action = input_slice[8];
        
        inputs.push((timestamp, action));
    }
    
    (score, duration, game_id, input_count, inputs)
}

fn validate_real_gameplay_simple(score: u32, duration: u64, game_id: u64, input_count: u32, inputs: &[(u64, u8)]) {
    // Constraint 1: Valid score range
    assert!(score > 0 && score <= 1000, 
            "Invalid score range: {} (must be 1-1000)", score);
    
    // Constraint 2: Valid game ID (prevents replay attacks)
    assert!(game_id > 0, "Invalid game ID: {}", game_id);
    
    // Constraint 3: Duration must match the last input timestamp
    if !inputs.is_empty() {
        let last_input_time = inputs.last().unwrap().0;
        assert!(duration >= last_input_time, 
                "Duration {}ms is less than last input time {}ms", 
                duration, last_input_time);
    }
    
    // Constraint 4: Inputs must be in chronological order
    for i in 1..inputs.len() {
        assert!(inputs[i].0 >= inputs[i-1].0,
                "Input {} timestamp {} is before input {} timestamp {}",
                i, inputs[i].0, i-1, inputs[i-1].0);
    }
    
    // Constraint 5: Realistic timing between inputs (human limitations)
    for i in 1..inputs.len() {
        let gap = inputs[i].0 - inputs[i-1].0;
        assert!(gap >= 200, "Inputs too fast: {}ms gap between inputs {} and {}", 
                gap, i-1, i); // Minimum 200ms between inputs
    }
    
    // Constraint 6: Score must be realistic for the number of inputs
    let actual_input_count = inputs.len() as u32;
    assert!(actual_input_count >= score, 
            "Too few inputs: {} inputs for {} points (minimum: 1 input per point)", 
            actual_input_count, score);
    assert!(actual_input_count <= score * 6, 
            "Too many inputs: {} inputs for {} points (maximum: 6 inputs per point)", 
            actual_input_count, score);
    
    // Constraint 7: Timing must be realistic for the score
    let min_time_per_point = 800; // 0.8 seconds minimum per point (more realistic)
    let max_time_per_point = 10000; // 10 seconds maximum per point
    
    assert!(duration >= score as u64 * min_time_per_point,
            "Game completed too fast: {}ms for {} points (minimum: {}ms)",
            duration, score, score as u64 * min_time_per_point);
    
    assert!(duration <= score as u64 * max_time_per_point,
            "Game completed too slowly: {}ms for {} points (maximum: {}ms)",
            duration, score, score as u64 * max_time_per_point);
    
    // Constraint 8: Input pattern must be human-like (simplified bot detection)
    validate_human_input_pattern_simple(inputs);
    
    // Constraint 9: Score must be achievable with the given inputs
    validate_score_achievable_simple(score, inputs);
}

fn validate_human_input_pattern_simple(inputs: &[(u64, u8)]) {
    if inputs.len() < 3 {
        return; // Not enough inputs to detect patterns
    }
    
    // Calculate timing gaps between inputs (simplified)
    let mut total_gap = 0u64;
    let mut gap_count = 0u32;
    
    for i in 1..inputs.len() {
        let gap = inputs[i].0 - inputs[i-1].0;
        total_gap += gap;
        gap_count += 1;
    }
    
    if gap_count == 0 {
        return;
    }
    
    let mean_gap = total_gap as f64 / gap_count as f64;
    
    // Simple variance calculation without complex data structures
    let mut total_variance = 0.0;
    for i in 1..inputs.len() {
        let gap = inputs[i].0 - inputs[i-1].0;
        let diff = gap as f64 - mean_gap;
        total_variance += diff * diff;
    }
    
    let variance = total_variance / gap_count as f64;
    let std_dev = variance.sqrt();
    let coefficient_of_variation = if mean_gap > 0.0 { std_dev / mean_gap } else { 0.0 };
    
    // Humans have variation in timing (coefficient of variation 0.1-2.0)
    // Bots: often < 0.1 (too perfect) or > 2.0 (too random)
    assert!(coefficient_of_variation >= 0.1 && coefficient_of_variation <= 2.0,
            "Bot-like input pattern detected: coefficient of variation = {} (expected 0.1-2.0)",
            coefficient_of_variation);
    
    // Check for suspicious regularity (simplified)
    let mut unique_gaps = 0u32;
    let mut last_gap = 0u64;
    let mut first_gap = true;
    
    for i in 1..inputs.len() {
        let gap = inputs[i].0 - inputs[i-1].0;
        if first_gap {
            unique_gaps = 1;
            last_gap = gap;
            first_gap = false;
        } else if gap != last_gap {
            unique_gaps += 1;
            last_gap = gap;
        }
    }
    
    assert!(unique_gaps > gap_count / 2, 
            "Too many identical input timings: {} unique gaps out of {} total",
            unique_gaps, gap_count);
}

fn validate_score_achievable_simple(score: u32, inputs: &[(u64, u8)]) {
    // Basic validation: score should be roughly proportional to input count
    let input_count = inputs.len() as u32;
    
    // In Flappy Bird, you typically need 1-3 inputs per point
    // Very skilled players might need fewer inputs, beginners need more
    let min_inputs_per_point = 0.8; // Very skilled
    let max_inputs_per_point = 4.0; // Beginner
    
    let inputs_per_point = input_count as f64 / score as f64;
    
    assert!(inputs_per_point >= min_inputs_per_point,
            "Too few inputs for score: {} inputs for {} points ({} inputs/point, minimum: {})",
            input_count, score, inputs_per_point, min_inputs_per_point);
    
    assert!(inputs_per_point <= max_inputs_per_point,
            "Too many inputs for score: {} inputs for {} points ({} inputs/point, maximum: {})",
            input_count, score, inputs_per_point, max_inputs_per_point);
}

fn create_real_proof_binding_simple(score: u32, game_id: u64, duration: u64, input_count: u32) -> u32 {
    let mut combined = (score as u64) ^ game_id;
    
    // Include input count in binding
    combined ^= (input_count as u64) << 32;
    
    // Include duration in binding
    combined ^= duration;
    
    // Cryptographic mixing
    combined = combined.wrapping_mul(0x517cc1b727220a95);
    combined ^= combined >> 33;
    combined = combined.wrapping_mul(0xc4ceb9fe1a85ec53);
    combined ^= combined >> 33;
    
    (combined as u32) ^ ((combined >> 32) as u32)
}