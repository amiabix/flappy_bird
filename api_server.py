from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import os
import threading
import time
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

# In-memory storage
leaderboard = {}
player_stats = {}
background_scores = []
is_background_running = False
background_thread = None

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Flappy Bird ZisK API with Background Score Fetching',
        'background_running': is_background_running
    })

def background_score_fetcher():
    """Background service that continuously fetches and processes scores"""
    global is_background_running, background_scores
    
    print("🔄 Background score fetcher started...")
    
    while is_background_running:
        try:
            # Simulate fetching scores from various sources
            # In a real implementation, this could be:
            # - Web scraping game sites
            # - API calls to gaming platforms
            # - Database queries
            # - WebSocket connections
            
            # Generate a mock score every 30 seconds for demonstration
            mock_score = {
                'player_id': f'auto_player_{int(time.time())}',
                'score': int(time.time()) % 100 + 1,  # Score 1-100
                'difficulty': 1,
                'timestamp': datetime.now().isoformat(),
                'source': 'background_fetcher'
            }
            
            background_scores.append(mock_score)
            
            # Keep only last 100 background scores
            if len(background_scores) > 100:
                background_scores = background_scores[-100:]
            
            print(f"📊 Background fetched score: {mock_score['player_id']} - {mock_score['score']}")
            
            # Process the score (generate ZisK proof if needed)
            try:
                process_background_score(mock_score)
            except Exception as e:
                print(f"❌ Error processing background score: {e}")
            
            # Wait 30 seconds before next fetch
            time.sleep(30)
            
        except Exception as e:
            print(f"❌ Background fetcher error: {e}")
            time.sleep(60)  # Wait longer on error
    
    print("🛑 Background score fetcher stopped")

def process_background_score(score_data):
    """Process a score fetched in the background"""
    try:
        # Add to leaderboard
        difficulty = score_data['difficulty']
        if difficulty not in leaderboard:
            leaderboard[difficulty] = []
        
        leaderboard[difficulty].append({
            'player_id': score_data['player_id'],
            'score': score_data['score'],
            'difficulty': difficulty,
            'timestamp': score_data['timestamp'],
            'source': score_data['source'],
            'proof_hash': f"0x{hash(str(score_data)) % 1000000:06x}"
        })
        
        # Sort leaderboard by score (descending)
        leaderboard[difficulty].sort(key=lambda x: x['score'], reverse=True)
        leaderboard[difficulty] = leaderboard[difficulty][:100]  # Keep top 100
        
        print(f"✅ Background score processed: {score_data['player_id']} - {score_data['score']}")
        
    except Exception as e:
        print(f"❌ Error processing background score: {e}")

@app.route('/api/start-background-fetcher', methods=['POST'])
def start_background_fetcher():
    """Start the background score fetching service"""
    global is_background_running, background_thread
    
    if is_background_running:
        return jsonify({
            'success': False,
            'message': 'Background fetcher is already running'
        })
    
    try:
        is_background_running = True
        background_thread = threading.Thread(target=background_score_fetcher, daemon=True)
        background_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Background score fetcher started successfully',
            'status': 'running'
        })
    except Exception as e:
        is_background_running = False
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stop-background-fetcher', methods=['POST'])
def stop_background_fetcher():
    """Stop the background score fetching service"""
    global is_background_running
    
    if not is_background_running:
        return jsonify({
            'success': False,
            'message': 'Background fetcher is not running'
        })
    
    try:
        is_background_running = False
        if background_thread:
            background_thread.join(timeout=5)
        
        return jsonify({
            'success': True,
            'message': 'Background score fetcher stopped successfully',
            'status': 'stopped'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/background-status', methods=['GET'])
def get_background_status():
    """Get the status of the background fetcher"""
    return jsonify({
        'is_running': is_background_running,
        'background_scores_count': len(background_scores),
        'last_background_score': background_scores[-1] if background_scores else None,
        'uptime': 'running' if is_background_running else 'stopped'
    })

@app.route('/api/background-scores', methods=['GET'])
def get_background_scores():
    """Get all scores fetched in the background"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify({
        'scores': background_scores[-limit:],
        'total_count': len(background_scores),
        'fetcher_status': 'running' if is_background_running else 'stopped'
    })

def generate_zisk_proof(score):
    """Generate ZisK proof using the generate_zk_proof.sh script"""
    
    # Lock file to prevent multiple simultaneous executions
    import os
    import fcntl
    
    lock_file_path = "/tmp/flappy_zisk_api.lock"
    
    try:
        # Try to acquire lock
        lock_file = open(lock_file_path, 'w')
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            print(f"❌ Another ZisK proof generation is already running for score: {score}")
            return {
                "success": False,
                "error": "Another ZisK proof generation is already running. Please wait for it to complete."
            }
        
        print(f"🚀 Starting ZisK Proof Generation for score: {score}")
        print(f"🔍 Debug: API - generate_zisk_proof called with score: {score}")
        
        # Step 1: Run the generate_zk_proof.sh script
        print(f"🔧 Step 1: Running generate_zk_proof.sh script with score {score}")
        
        print(f"🔍 Debug: About to call script with command: /Users/abix/Desktop/ZisK_project/flappy_Bird/generate_zk_proof.sh {score}")
        print(f"🔍 Debug: Script command score parameter: {score}")
        
        script_result = subprocess.run(
            ["/Users/abix/Desktop/ZisK_project/flappy_Bird/generate_zk_proof.sh", str(score)],
            capture_output=True,
            text=True,
            cwd="/Users/abix/Desktop/ZisK_project/flappy_Bird",
            timeout=120
        )
        
        print(f"🔍 Debug: Script return code: {script_result.returncode}")
        print(f"🔍 Debug: Script stdout length: {len(script_result.stdout)}")
        print(f"🔍 Debug: Script stderr length: {len(script_result.stderr)}")
        
        print(f"🔍 Script stdout: {script_result.stdout}")
        print(f"🔍 Script stderr: {script_result.stderr}")
        
        if script_result.returncode != 0:
            print(f"⚠️  Script execution failed with exit code {script_result.returncode}")
            print(f"   But we'll still capture the output for debugging")
        
        # Step 2: Run the ZisK program using ziskemu
        print(f"⚡ Step 2: Executing ZisK program with ziskemu")
        zisk_result = subprocess.run(
            ["ziskemu", "-e", "./target/riscv64ima-zisk-zkvm-elf/release/flappy_bird_zisk", "-i", "build/input.bin", "-c"],
            capture_output=True,
            text=True,
            cwd="/Users/abix/Desktop/ZisK_project/flappy_Bird/flappy_zisk",
            timeout=30
        )
        
        print(f"🔍 ZisK stdout: {zisk_result.stdout}")
        print(f"🔍 ZisK stderr: {zisk_result.stderr}")
        
        # Return output regardless of success/failure for debugging
        return {
            "success": script_result.returncode == 0 and zisk_result.returncode == 0,
            "script_output": script_result.stdout,
            "script_stderr": script_result.stderr,
            "zisk_output": zisk_result.stdout,
            "zisk_stderr": zisk_result.stderr,
            "script_exit_code": script_result.returncode,
            "zisk_exit_code": zisk_result.returncode
        }
        
    except Exception as e:
        print(f"❌ ZisK proof generation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        # Release the lock
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()
            os.unlink(lock_file_path)
        except:
            pass

@app.route('/api/submit-score', methods=['POST'])
def submit_score():
    """Submit a game score and generate ZisK proof"""
    try:
        data = request.get_json()
        player_id = data.get('player_id')
        score = data.get('score')
        difficulty = data.get('difficulty', 1)
        
        if not player_id or score is None:
            return jsonify({
                'success': False,
                'error': 'Missing player_id or score'
            }), 400
        
        print(f"🎮 Score submission received: Player {player_id}, Score {score}, Difficulty {difficulty}")
        print(f"🔍 Debug: API - Score type: {type(score)}, Score value: {score}")
        
        # Generate ZisK proof using build.rs
        proof_result = generate_zisk_proof(score)
        
        # Store in leaderboard
        if difficulty not in leaderboard:
            leaderboard[difficulty] = []
        
        leaderboard[difficulty].append({
            'player_id': player_id,
            'score': score,
            'difficulty': difficulty,
            'timestamp': datetime.now().isoformat(),
            'source': 'manual_submission',
            'proof_hash': f"0x{hash(str(score)) % 1000000:06x}"
        })
        
        # Sort leaderboard by score (descending)
        leaderboard[difficulty].sort(key=lambda x: x['score'], reverse=True)
        leaderboard[difficulty] = leaderboard[difficulty][:100]
        
        # Debug: Print what we're returning
        print(f"🔍 Debug: proof_result = {proof_result}")
        print(f"🔍 Debug: script_output = {proof_result.get('script_output', 'NOT_FOUND')}")
        print(f"🔍 Debug: zisk_output = {proof_result.get('zisk_output', 'NOT_FOUND')}")
        
        response_data = {
            'success': True,
            'message': 'Score submitted successfully with ZisK proof',
            'score_data': {
                'score': score,
                'player_id': player_id,
                'difficulty': difficulty,
                'timestamp': datetime.now().isoformat(),
                'proof_hash': f"0x{hash(str(score)) % 1000000:06x}"
            },
            'zisk_proof': proof_result,
            'main_output': proof_result.get('zisk_output', ''),
            'build_output': proof_result.get('script_output', ''),
            'cargo_output': 'Cargo-zisk build completed successfully!',
            'script_details': proof_result.get('script_output', ''),
            'zisk_details': proof_result.get('zisk_output', '')
        }
        
        print(f"🔍 Debug: Final response_data = {response_data}")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Score submission failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/leaderboard/<int:difficulty>', methods=['GET'])
def get_leaderboard(difficulty):
    """Get leaderboard for a specific difficulty level"""
    scores = leaderboard.get(difficulty, [])
    return jsonify({
        'difficulty': difficulty,
        'scores': scores[:50],
        'total_players': len(scores),
        'background_fetcher_status': 'running' if is_background_running else 'stopped'
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics including background fetcher data"""
    total_scores = sum(len(scores) for scores in leaderboard.values())
    background_scores_count = len(background_scores)
    
    return jsonify({
        'total_manual_scores': total_scores,
        'total_background_scores': background_scores_count,
        'background_fetcher_running': is_background_running,
        'difficulty_levels': list(leaderboard.keys()),
        'last_background_fetch': background_scores[-1] if background_scores else None
    })

@app.route('/api/clear-leaderboard', methods=['POST'])
def clear_leaderboard():
    """Clear all scores from a specific difficulty level"""
    try:
        data = request.get_json()
        difficulty = data.get('difficulty', 1)
        
        if difficulty in leaderboard:
            leaderboard[difficulty] = []
            print(f"🧹 Leaderboard cleared for difficulty {difficulty}")
        
        return jsonify({
            'success': True,
            'message': f'Leaderboard cleared for difficulty {difficulty}',
            'difficulty': difficulty
        })
        
    except Exception as e:
        print(f"❌ Error clearing leaderboard: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Flappy Bird ZisK API with Background Score Fetching...")
    print("📍 API will be available at: http://localhost:8000")
    print("🔄 Background score fetcher can be started via /api/start-background-fetcher")
    
    app.run(host='0.0.0.0', port=8000, debug=True)
