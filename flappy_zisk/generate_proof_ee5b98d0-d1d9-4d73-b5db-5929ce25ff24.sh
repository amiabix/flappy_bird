#!/bin/bash
cd /home/ayush/Examples/flappy_bird/flappy_zisk
echo "Generating proof for score 0"
cargo-zisk build --release
cargo run --bin generate_simple_input --release
ziskemu target/zisk/release/flappy_zisk
echo "Proof generation completed"
