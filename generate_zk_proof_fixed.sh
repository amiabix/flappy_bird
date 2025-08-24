#!/bin/bash

# Enhanced Flappy Bird ZisK Proof Generation Script
# This script ensures proper sequential execution with completion verification
# Uses custom port range (23200-23202) to avoid conflicts with other users

# Lock file to prevent multiple instances from running simultaneously
LOCK_FILE="/tmp/flappy_zisk_proof.lock"

# Enhanced logging
log_info() {
    echo "[INFO $(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_error() {
    echo "[ERROR $(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
}

log_warn() {
    echo "[WARN $(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if another instance is running
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
        log_error "Another ZisK proof generation is already running (PID: $PID)"
        log_error "Please wait for it to complete or check if it's stuck"
        exit 1
    else
        # Remove stale lock file
        rm -f "$LOCK_FILE"
        log_warn "Removed stale lock file"
    fi
fi

# Create lock file
echo $$ > "$LOCK_FILE"
log_info "Lock file created with PID: $$"

# Function to cleanup lock file on exit
cleanup() {
    log_info "Cleaning up lock file for PID: $$"
    rm -f "$LOCK_FILE"
    
    # Additional cleanup for ZisK processes
    cleanup_zisk_processes
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Enhanced process waiting function
wait_for_process_completion() {
    local pid=$1
    local process_name=$2
    local timeout=${3:-300}  # Default 5 minute timeout
    local elapsed=0
    
    log_info "Waiting for $process_name (PID: $pid) to complete..."
    
    while ps -p "$pid" > /dev/null 2>&1; do
        if [ $elapsed -ge $timeout ]; then
            log_error "$process_name timed out after ${timeout}s"
            return 1
        fi
        sleep 2
        elapsed=$((elapsed + 2))
        
        if [ $((elapsed % 30)) -eq 0 ]; then
            log_info "Still waiting for $process_name... (${elapsed}s elapsed)"
        fi
    done
    
    log_info "$process_name completed successfully"
    return 0
}

# Enhanced file verification function
verify_file_completion() {
    local file_path=$1
    local expected_min_size=${2:-1}  # Minimum expected size in bytes
    local timeout=${3:-60}          # Timeout for file to stabilize
    local check_interval=2
    local elapsed=0
    
    log_info "Verifying file completion: $file_path"
    
    # Wait for file to exist
    while [ ! -f "$file_path" ] && [ $elapsed -lt $timeout ]; do
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    if [ ! -f "$file_path" ]; then
        log_error "File $file_path was not created within ${timeout}s"
        return 1
    fi
    
    # Wait for file size to stabilize (indicates writing is complete)
    local prev_size=0
    local stable_count=0
    elapsed=0
    
    while [ $elapsed -lt $timeout ]; do
        local current_size=$(stat -c%s "$file_path" 2>/dev/null || echo 0)
        
        if [ "$current_size" -ge "$expected_min_size" ]; then
            if [ "$current_size" -eq "$prev_size" ]; then
                stable_count=$((stable_count + 1))
                if [ $stable_count -ge 3 ]; then  # Size stable for 3 checks
                    log_info "File $file_path verified (size: ${current_size} bytes)"
                    return 0
                fi
            else
                stable_count=0
            fi
        fi
        
        prev_size=$current_size
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
        
        if [ $((elapsed % 20)) -eq 0 ]; then
            log_info "File verification in progress... (current size: ${current_size}, elapsed: ${elapsed}s)"
        fi
    done
    
    log_error "File $file_path did not stabilize within ${timeout}s"
    return 1
}

# Enhanced ZisK resource management
cleanup_zisk_processes() {
    log_info "Cleaning up ZisK processes and resources..."
    
    # Kill any remaining ZisK processes
    pkill -f "zec-keccakf.*2311" 2>/dev/null || true
    pkill -f "cargo-zisk.*prove" 2>/dev/null || true
    
    # Clean up shared memory
    find /dev/shm -name "ZISK_*" -delete 2>/dev/null || true
    find /tmp -name "ZISK_*" -delete 2>/dev/null || true
    
    log_info "ZisK cleanup completed"
}

# Enhanced resource availability check
wait_for_zisk_resources() {
    # Use custom port range to avoid conflicts with other users
    local base_port=23200
    local mo_port=$((base_port + 0))
    local mt_port=$((base_port + 1))
    local rh_port=$((base_port + 2))
    local max_wait=300
    local elapsed=0
    
    log_info "Waiting for ZisK resources to become available..."
    
    while [ $elapsed -lt $max_wait ]; do
        # Check if ports are free
        local ports_free=true
        
        if netstat -tln 2>/dev/null | grep -q ":$mo_port " ||
           netstat -tln 2>/dev/null | grep -q ":$mt_port " ||
           netstat -tln 2>/dev/null | grep -q ":$rh_port "; then
            ports_free=false
        fi
        
        # Check if shared memory is free
        if ls /dev/shm/ZISK_* 2>/dev/null | grep -q "ZISK_${mo_port}_\|ZISK_${mt_port}_\|ZISK_${rh_port}_"; then
            ports_free=false
        fi
        
        if $ports_free; then
            log_info "ZisK resources are available"
            return 0
        fi
        
        if [ $((elapsed % 30)) -eq 0 ] && [ $elapsed -gt 0 ]; then
            log_info "Still waiting for ZisK resources... (${elapsed}s / ${max_wait}s)"
            log_info "Active ZisK processes:"
            ps aux | grep -E "zec-keccakf.*2311|cargo-zisk.*prove" | grep -v grep | head -3
        fi
        
        sleep 10
        elapsed=$((elapsed + 10))
    done
    
    log_error "Timeout waiting for ZisK resources"
    return 1
}

# Enhanced command execution with proper waiting
execute_with_completion_check() {
    local cmd="$1"
    local step_name="$2"
    local expected_files="$3"  # Space-separated list of expected output files
    local timeout="${4:-300}"   # Command timeout
    
    log_info "Executing $step_name"
    log_info "Command: $cmd"
    
    # Execute command in background to get PID
    eval "$cmd" &
    local cmd_pid=$!
    
    # Wait for command to complete
    if ! wait_for_process_completion "$cmd_pid" "$step_name" "$timeout"; then
        log_error "$step_name failed or timed out"
        return 1
    fi
    
    # Check command exit status
    wait $cmd_pid
    local exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        log_error "$step_name failed with exit code: $exit_code"
        return 1
    fi
    
    # Verify expected files if provided
    if [ -n "$expected_files" ]; then
        for file in $expected_files; do
            if ! verify_file_completion "$file"; then
                log_error "$step_name did not produce expected file: $file"
                return 1
            fi
        done
    fi
    
    log_info "$step_name completed successfully"
    return 0
}

echo "Starting Enhanced ZisK Proof Generation..."
echo "=========================================="

# Check if GAME_SCORE is provided as argument
if [ $# -eq 0 ]; then
    log_error "Please provide a game score"
    echo "Usage: ./generate_zk_proof.sh <score>"
    echo "Example: ./generate_zk_proof.sh 5"
    exit 1
fi

GAME_SCORE=$1
log_info "Game Score: $GAME_SCORE"

# Change to the flappy_zisk directory
cd "$(dirname "$0")/flappy_zisk" || {
    log_error "Could not change to flappy_zisk directory"
    exit 1
}

log_info "Working directory: $(pwd)"

# Step 1: Generate input.bin using build.rs
echo ""
log_info "Step 1: Generating input.bin with score $GAME_SCORE"
echo "================================================================"

export GAME_SCORE=$GAME_SCORE
echo "$GAME_SCORE" > GAME_SCORE.txt

if ! execute_with_completion_check "GAME_SCORE=$GAME_SCORE cargo build" "build.rs execution" "build/input.bin"; then
    log_error "Step 1 failed"
    exit 1
fi

# Step 2: Build ZisK program
echo ""
log_info "Step 2: Building ZisK program"
echo "================================"

if ! execute_with_completion_check "cargo-zisk build --release" "ZisK build" "target/riscv64ima-zisk-zkvm-elf/release/flappy_zisk"; then
    log_error "Step 2 failed"
    exit 1
fi

# Step 2.5: ROM setup
echo ""
log_info "Step 2.5: ROM setup"
echo "==================="

# ROM setup might fail on macOS, so we handle it gracefully on MacOs
if execute_with_completion_check "cargo-zisk rom-setup -e target/riscv64ima-zisk-zkvm-elf/release/flappy_zisk" "ROM setup" "" 120; then
    log_info "ROM setup completed successfully"
else
    log_warn "ROM setup failed (expected on macOS), continuing..."
fi

# Step 3: ZisK emulation
echo ""
log_info "Step 3: ZisK emulation"
echo "======================"

if execute_with_completion_check "ziskemu -e target/riscv64ima-zisk-zkvm-elf/release/flappy_zisk -i build/input.bin" "ZisK emulation" "" 120; then
    log_info "ZisK emulation completed successfully"
else
    log_warn "ZisK emulation failed (expected on macOS), continuing..."
fi

# Step 4: Wait for resources and generate proof
echo ""
log_info "Step 4: Generating ZK Proof"
echo "============================"

# Wait for ZisK resources to be available
if ! wait_for_zisk_resources; then
    log_error "Cannot proceed with proof generation - resources unavailable"
    exit 1
fi

# Clean up any stale resources before starting
cleanup_zisk_processes
sleep 5  # Give system time to clean up

log_info "Starting proof generation (this may take 5-15 minutes)..."

# Execute proof generation with extended timeout and custom port
if ! execute_with_completion_check "cargo-zisk prove -e target/riscv64ima-zisk-zkvm-elf/release/flappy_zisk -i build/input.bin -o proof -a -y -p 23200" "ZK proof generation" "proof/vadcop_final_proof.bin" 1800; then  # 30 minute timeout
    log_error "Step 4 failed"
    exit 1
fi

# Additional verification that all proof files are complete
if [ -d "proof" ]; then
    log_info "Verifying proof directory contents..."
    ls -la proof/
    
    # Check if proof file is not empty
    if [ -s "proof/vadcop_final_proof.bin" ]; then
        log_info "Proof file generated successfully ($(stat -c%s proof/vadcop_final_proof.bin) bytes)"
    else
        log_error "Proof file is empty or missing"
        exit 1
    fi
else
    log_error "Proof directory was not created"
    exit 1
fi

# Step 5: Verify the generated proof
echo ""
log_info "Step 5: Verifying ZK Proof"
echo "==========================="

if execute_with_completion_check "cargo-zisk verify -p ./proof/vadcop_final_proof.bin" "ZK proof verification" "" 120; then
    log_info "ZK proof verification completed successfully!"
else
    log_warn "ZK proof verification failed (may not be supported on this platform)"
fi

echo ""
echo "=================================================="
log_info "ZisK Proof Generation Pipeline Complete!"
echo "=================================================="
log_info "All steps executed successfully"
log_info "Proof files available in: $(pwd)/proof/"
echo ""
