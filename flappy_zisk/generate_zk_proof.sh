#!/bin/bash

# Simple ZisK proof generation script
# Usage: ./generate_zk_proof.sh <score>

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <score>"
    exit 1
fi

SCORE=$1
echo "🎯 Generating ZisK proof for score: $SCORE"

# Set the game score
echo "$SCORE" > GAME_SCORE.txt

# Build the ZisK program
echo "🔨 Building ZisK program..."
cargo-zisk build --release

# Generate input file
echo "📝 Generating input file..."
cargo run --bin generate_simple_input --release

# Run ZisK to generate proof
echo "🚀 Running ZisK proof generation..."
ziskemu target/zisk/release/flappy_zisk

echo "✅ ZisK proof generation completed!"
echo "📁 Proof files generated in: proof/"

# Check if proof was generated
if [ -f "proof/vadcop_final_proof.bin" ]; then
    echo "🎉 SUCCESS: Proof file generated!"
    ls -la proof/
else
    echo "❌ ERROR: Proof file not found!"
    exit 1
fi
