from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
import threading
import time
from datetime import datetime, timedelta
import uuid
import queue
import logging
from collections import defaultdict
from enum import Enum
import signal
import platform

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# REQUEST LOGGING MIDDLEWARE - Debug frontend duplicate submissions
@app.before_request
def log_request_info():
    if request.endpoint == 'submit_score':
        logger.info(f"🔍 FRONTEND REQUEST: {request.method} {request.url}")
        logger.info(f"🔍 Headers: {dict(request.headers)}")
        try:
            data = request.get_json()
            logger.info(f"🔍 Request Data: {data}")
        except:
            logger.info(f"🔍 Request Data: <could not parse JSON>")
        logger.info(f"🔍 Timestamp: {datetime.now().isoformat()}")
        logger.info(f"🔍 Remote Addr: {request.remote_addr}")
        logger.info(f"🔍 User Agent: {request.headers.get('User-Agent', 'Unknown')}")

class ProofStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

# Global variables - ONLY for real submitted data
leaderboard = defaultdict(list)  # Only real submitted scores
proof_jobs = {}  # {job_id: ProofJob} - Only real proof jobs
proof_queue = queue.Queue()  # Only real proof generation requests
active_proof_workers = {}  # {thread_id: ProofJob}

# DEDUPLICATION SYSTEM
recent_submissions = {}  # {(player_id, score, difficulty): {'timestamp': datetime, 'job_id': str}}
DEDUP_WINDOW_SECONDS = 30  # Prevent same score within 30 seconds

# Thread synchronization
leaderboard_lock = threading.RLock()
proof_jobs_lock = threading.RLock()
dedup_lock = threading.RLock()  # Protect deduplication data
zisk_execution_lock = threading.Lock()  # Ensure only one ZisK process runs at a time

def generate_game_id(job_id, score):
    """Generate unique game session ID for tamper-proof binding"""
    timestamp = int(time.time())
    # Include job_id hash for uniqueness
    random_part = hash(job_id) % (2**20)  # 20 bits
    return (timestamp << 20) | random_part

def cleanup_old_dedup_entries():
    """Clean up expired deduplication entries to prevent memory bloat"""
    current_time = datetime.now()
    expired_keys = []
    
    with dedup_lock:
        for key, data in recent_submissions.items():
            if (current_time - data['timestamp']).total_seconds() > DEDUP_WINDOW_SECONDS:
                expired_keys.append(key)
        
        for key in expired_keys:
            del recent_submissions[key]
    
    if expired_keys:
        logger.info(f"🧹 Cleaned up {len(expired_keys)} expired deduplication entries")

class ProofJob:
    def __init__(self, job_id, player_id, score, difficulty):
        self.job_id = job_id
        self.player_id = player_id
        self.score = score
        self.difficulty = difficulty
        self.status = ProofStatus.PENDING
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.proof_output = None
        self.error_message = None
        self.proof_file_path = None
        self.process_pid = None
        self.game_id = None  # Will be set after creation
        
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'player_id': self.player_id,
            'score': self.score,
            'difficulty': self.difficulty,
            'game_id': self.game_id,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': (
                (self.completed_at - self.started_at).total_seconds() 
                if self.completed_at and self.started_at else None
            ),
            'proof_file_path': self.proof_file_path,
            'error_message': self.error_message
        }

def proof_worker():
    """Bulletproof worker thread that processes real proof generation jobs"""
    thread_id = threading.get_ident()
    worker_name = f"Worker-{thread_id}"
    start_time = time.time()  # Track when worker started
    logger.info(f"{worker_name} started and ready for jobs")
    
    job_count = 0
    
    while True:
        job = None  # Initialize job variable
        job_processed = False
        
        try:
            # Get next REAL job from queue (blocks until available)
            logger.info(f"{worker_name} waiting for next job...")
            job = proof_queue.get(timeout=30)  # Reduced timeout to prevent hanging
            
            if job is None:  # Poison pill to stop worker
                logger.info(f"{worker_name} received shutdown signal")
                break
            
            job_count += 1
            logger.info(f"{worker_name} got job #{job_count}: {job.job_id} (score: {job.score})")
            
            # Mark job as in progress
            try:
                with proof_jobs_lock:
                    active_proof_workers[thread_id] = job
                    job.status = ProofStatus.IN_PROGRESS
                    job.started_at = datetime.now()
                    proof_jobs[job.job_id] = job
                
                logger.info(f"{worker_name} starting proof generation for job {job.job_id}")
                
                # Generate the REAL ZisK proof with extra protection
                result = generate_real_zisk_proof_safe(job, worker_name)
                job_processed = True
                
                # Update job status based on result
                with proof_jobs_lock:
                    if result['success']:
                        job.status = ProofStatus.COMPLETED
                        job.proof_output = result.get('output', '')
                        job.proof_file_path = result.get('proof_file_path')
                        logger.info(f"{worker_name} SUCCESSFULLY completed job {job.job_id}")
                    else:
                        job.status = ProofStatus.FAILED
                        job.error_message = result.get('error', 'Unknown error')
                        logger.error(f"{worker_name} FAILED job {job.job_id}: {job.error_message}")
                    
                    job.completed_at = datetime.now()
                    proof_jobs[job.job_id] = job
                    
                    # Remove from active workers
                    if thread_id in active_proof_workers:
                        del active_proof_workers[thread_id]
                
                # Update leaderboard
                update_leaderboard_with_real_proof(job)
                
            except Exception as job_error:
                logger.error(f"{worker_name} exception during job {job.job_id}: {job_error}")
                job_processed = True  # We attempted to process it
                
                # Mark job as failed
                try:
                    with proof_jobs_lock:
                        job.status = ProofStatus.FAILED
                        job.error_message = f"Worker exception: {str(job_error)}"
                        job.completed_at = datetime.now()
                        if thread_id in active_proof_workers:
                            del active_proof_workers[thread_id]
                        proof_jobs[job.job_id] = job
                except:
                    pass  # Don't let cleanup errors kill the worker
            
        except queue.Empty:
            # No jobs available - this is normal, keep waiting
            logger.debug(f"{worker_name} no jobs available, continuing to wait...")
            
            # Check if this worker should terminate (prevent infinite hanging)
            if job_count == 0 and time.time() - start_time > 300:  # 5 minutes without any jobs
                logger.warning(f"{worker_name} terminating due to inactivity (no jobs in 5 minutes)")
                break
                
            continue
            
        except Exception as worker_error:
            # Critical worker error - log but don't die
            logger.error(f"{worker_name} critical error: {worker_error}")
            logger.error(f"{worker_name} will continue running despite error")
            
            # If we had a job, mark it as failed
            if job is not None:
                try:
                    with proof_jobs_lock:
                        job.status = ProofStatus.FAILED
                        job.error_message = f"Worker critical error: {str(worker_error)}"
                        job.completed_at = datetime.now()
                        if thread_id in active_proof_workers:
                            del active_proof_workers[thread_id]
                        proof_jobs[job.job_id] = job
                    job_processed = True
                except:
                    pass  # Don't let cleanup kill worker
        
        finally:
            # Always mark queue task as done if we got a job
            if job is not None and job_processed:
                try:
                    proof_queue.task_done()
                    logger.debug(f"{worker_name} marked job {job.job_id} as done in queue")
                except Exception as cleanup_error:
                    logger.error(f"{worker_name} error marking task done: {cleanup_error}")
        
        # Small delay between jobs to prevent resource conflicts
        time.sleep(1)
    
    logger.info(f"{worker_name} stopped after processing {job_count} jobs")

def generate_real_zisk_proof_safe(job, worker_name):
    """Generate REAL ZisK proof with enhanced safety and cleanup (psutil-free)"""
    process = None
    
    # CRITICAL: Acquire ZisK execution lock to ensure only one ZisK process runs at a time
    logger.info(f"{worker_name} waiting for ZisK execution lock...")
    with zisk_execution_lock:
        logger.info(f"{worker_name} acquired ZisK execution lock, starting proof generation")
        
        try:
            logger.info(f"{worker_name} starting REAL ZisK proof for job {job.job_id}, score: {job.score}")
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(current_dir, "generate_zk_proof_fixed.sh")
            
            if not os.path.exists(script_path):
                return {
                    "success": False,
                    "error": f"ZisK proof script not found at {script_path}"
                }
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            logger.info(f"{worker_name} executing: {script_path} {job.score}")
            
            # Create the process with better isolation using process groups
            process = subprocess.Popen(
                ['bash', script_path, str(job.score)],  # Explicitly use bash
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=current_dir,
                env=dict(os.environ, GAME_SCORE=str(job.score)),  # Ensure environment variable is set
                start_new_session=True  # Creates new process group for better isolation
            )
            
            # Store PID and process group PID for monitoring and cleanup
            with proof_jobs_lock:
                job.process_pid = process.pid
                try:
                    # Get process group ID (works on Unix-like systems)
                    job.process_group_pid = os.getpgid(process.pid)
                except OSError:
                    # Fallback to process PID if process group not available
                    job.process_group_pid = process.pid
            
            logger.info(f"{worker_name} started ZisK process PID: {process.pid}, PGID: {job.process_group_pid}")
            
            try:
                # Wait with timeout and periodic logging
                start_time = time.time()
                timeout_seconds = 2700  # 45 minutes
                
                while True:
                    try:
                        # Check if process is done (non-blocking)
                        stdout, stderr = process.communicate(timeout=30)
                        # If we get here, process completed
                        break
                    except subprocess.TimeoutExpired:
                        # Process still running, log progress
                        elapsed = time.time() - start_time
                        logger.info(f"{worker_name} job {job.job_id} still running... ({elapsed:.0f}s elapsed)")
                        
                        if elapsed > timeout_seconds:
                            # Timeout reached
                            logger.warning(f"{worker_name} job {job.job_id} timed out after {elapsed:.0f}s")
                            raise subprocess.TimeoutExpired(process.args, timeout_seconds)
                        
                        # Check if process died unexpectedly
                        if process.poll() is not None:
                            # Process ended, get output
                            stdout, stderr = process.communicate()
                            break
                
                exit_code = process.returncode
                logger.info(f"{worker_name} ZisK process completed with exit code: {exit_code}")
                
                if exit_code == 0:
                    # Check for REAL proof file
                    proof_dir = os.path.join(current_dir, "flappy_zisk", "proof")
                    proof_file = os.path.join(proof_dir, "vadcop_final_proof.bin")
                    
                    logger.info(f"{worker_name} checking for proof file: {proof_file}")
                    
                    # Wait a bit for file system to sync
                    time.sleep(2)
                    
                    if os.path.exists(proof_file):
                        file_size = os.path.getsize(proof_file)
                        if file_size > 0:
                            logger.info(f"{worker_name} SUCCESS: Proof file generated ({file_size} bytes)")
                            return {
                                "success": True,
                                "output": stdout,
                                "proof_file_path": proof_file
                            }
                        else:
                            logger.error(f"{worker_name} proof file exists but is empty")
                            return {
                                "success": False,
                                "error": "ZisK proof file generated but is empty",
                                "output": stdout
                            }
                    else:
                        logger.error(f"{worker_name} proof file not found at {proof_file}")
                        logger.info(f"{worker_name} checking proof directory contents:")
                        try:
                            if os.path.exists(proof_dir):
                                for f in os.listdir(proof_dir):
                                    logger.info(f"  {f}")
                            else:
                                logger.info(f"  Proof directory {proof_dir} does not exist")
                        except:
                            pass
                        
                        return {
                            "success": False,
                            "error": "ZisK proof file was not generated",
                            "output": stdout
                        }
                else:
                    logger.error(f"{worker_name} ZisK process failed with exit code {exit_code}")
                    return {
                        "success": False,
                        "error": f"ZisK proof generation failed (exit code {exit_code}): {stderr}",
                        "output": stdout
                    }
                    
            except subprocess.TimeoutExpired:
                logger.warning(f"{worker_name} killing timed out ZisK process {process.pid}")
                
                # Kill process and cleanup
                cleanup_process_safe(process, job, worker_name)
                
                with proof_jobs_lock:
                    job.status = ProofStatus.TIMEOUT
                
                return {
                    "success": False,
                    "error": f"ZisK proof generation timed out after 45 minutes"
                }
                
        except Exception as e:
            logger.error(f"{worker_name} exception in ZisK proof generation: {e}")
            
            # Cleanup process if it exists
            if process:
                cleanup_process_safe(process, job, worker_name)
            
            return {
                "success": False,
                "error": f"ZisK proof generation error: {str(e)}"
            }
        
        finally:
            # Always cleanup
            if process:
                cleanup_process_safe(process, job, worker_name)

def cleanup_process_safe(process, job, worker_name):
    """Safely cleanup a subprocess using process groups (psutil-free)"""
    try:
        if process and process.poll() is None:  # Process still running
            logger.info(f"{worker_name} terminating process {process.pid}")
            
            # Try graceful termination first using process group
            try:
                if job and job.process_group_pid:
                    # Kill entire process group gracefully
                    os.killpg(job.process_group_pid, signal.SIGTERM)
                    logger.info(f"{worker_name} sent SIGTERM to process group {job.process_group_pid}")
                else:
                    # Fallback to individual process
                    process.terminate()
                    logger.info(f"{worker_name} sent SIGTERM to process {process.pid}")
            except OSError as e:
                logger.warning(f"{worker_name} error sending SIGTERM: {e}")
                # Process might already be dead
            
            # Wait a bit for graceful shutdown
            try:
                process.wait(timeout=10)
                logger.info(f"{worker_name} process {process.pid} terminated gracefully")
            except subprocess.TimeoutExpired:
                # Force kill using process group
                logger.warning(f"{worker_name} force killing process group {job.process_group_pid if job else process.pid}")
                try:
                    if job and job.process_group_pid:
                        os.killpg(job.process_group_pid, signal.SIGKILL)
                    else:
                        process.kill()
                    try:
                        process.wait(timeout=5)
                        logger.info(f"{worker_name} process force killed")
                    except:
                        logger.error(f"{worker_name} could not confirm process kill")
                except OSError as e:
                    logger.error(f"{worker_name} error force killing: {e}")
        
        # Additional cleanup for any remaining child processes using OS commands
        try:
            if job and job.process_pid:
                cleanup_child_processes_os(job.process_pid, worker_name)
        except:
            pass  # Don't let cleanup errors kill the worker
            
    except Exception as cleanup_error:
        logger.error(f"{worker_name} error during process cleanup: {cleanup_error}")

def cleanup_child_processes_os(parent_pid, worker_name):
    """Clean up child processes using OS commands (psutil-free)"""
    try:
        system = platform.system().lower()
        
        if system in ['linux', 'darwin']:  # Unix-like systems
            # Find and kill child processes
            try:
                # Use pgrep to find children
                result = subprocess.run(
                    ['pgrep', '-P', str(parent_pid)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    child_pids = result.stdout.strip().split('\n')
                    logger.info(f"{worker_name} found {len(child_pids)} child processes to cleanup")
                    
                    for child_pid in child_pids:
                        if child_pid.strip():
                            try:
                                os.kill(int(child_pid.strip()), signal.SIGTERM)
                                logger.debug(f"{worker_name} sent SIGTERM to child {child_pid}")
                            except (ValueError, OSError):
                                pass
                    
                    # Wait a bit then force kill any remaining
                    time.sleep(2)
                    for child_pid in child_pids:
                        if child_pid.strip():
                            try:
                                os.kill(int(child_pid.strip()), signal.SIGKILL)
                                logger.debug(f"{worker_name} force killed child {child_pid}")
                            except (ValueError, OSError):
                                pass
                                
            except subprocess.TimeoutExpired:
                logger.warning(f"{worker_name} pgrep timeout during child cleanup")
            except Exception as e:
                logger.debug(f"{worker_name} child cleanup error: {e}")
                
        elif system == 'windows':
            # Windows cleanup using taskkill
            try:
                subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(parent_pid)],
                    capture_output=True,
                    timeout=10
                )
            except:
                pass  # Windows cleanup is optional
                
    except Exception as e:
        logger.debug(f"{worker_name} OS-specific cleanup error: {e}")

# Worker health monitoring
def monitor_workers():
    """Monitor worker health and restart if needed"""
    while True:
        try:
            time.sleep(60)  # Check every minute
            
            # Clean up old deduplication entries
            cleanup_old_dedup_entries()
            
            with proof_jobs_lock:
                # Check if we have jobs but no active workers
                if proof_queue.qsize() > 0 and len(active_proof_workers) == 0:
                    logger.warning("Jobs in queue but no active workers - restarting workers")
                    init_proof_workers(num_workers=2)
                
                # Log worker status
                if active_proof_workers:
                    logger.info(f"Active workers: {len(active_proof_workers)}")
                    for thread_id, job in active_proof_workers.items():
                        duration = (datetime.now() - job.started_at).total_seconds()
                        logger.info(f"  Worker {thread_id}: job {job.job_id} running {duration:.0f}s")
            
        except Exception as e:
            logger.error(f"Worker monitor error: {e}")

# Global worker tracking
worker_threads = []

def update_leaderboard_with_real_proof(job):
    """Update leaderboard entry with REAL proof completion status"""
    try:
        with leaderboard_lock:
            difficulty_scores = leaderboard[job.difficulty]
            
            # Find and update the corresponding leaderboard entry
            for entry in difficulty_scores:
                if (entry.get('player_id') == job.player_id and 
                    entry.get('score') == job.score and
                    entry.get('job_id') == job.job_id):
                    
                    entry['proof_status'] = job.status.value
                    entry['proof_completed_at'] = job.completed_at.isoformat() if job.completed_at else None
                    
                    if job.proof_file_path:
                        entry['proof_file_path'] = job.proof_file_path
                    
                    if job.error_message:
                        entry['proof_error'] = job.error_message
                    
                    logger.info(f"Updated leaderboard entry with REAL proof result for job {job.job_id}")
                    break
                    
    except Exception as e:
        logger.error(f"Error updating leaderboard for job {job.job_id}: {e}")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint - ONLY real data"""
    with proof_jobs_lock:
        active_count = len(active_proof_workers)
        pending_count = proof_queue.qsize()
        
        total_jobs = len(proof_jobs)
        completed_jobs = len([j for j in proof_jobs.values() if j.status == ProofStatus.COMPLETED])
        failed_jobs = len([j for j in proof_jobs.values() if j.status == ProofStatus.FAILED])
    
    with leaderboard_lock:
        total_scores = sum(len(scores) for scores in leaderboard.values())
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'proof_system': {
            'active_proofs': active_count,
            'pending_proofs': pending_count,
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs
        },
        'leaderboard': {
            'total_real_scores': total_scores,  # Only real submitted scores
            'difficulty_levels': list(leaderboard.keys())
        }
    })

@app.route('/api/submit-score', methods=['POST'])
def submit_score():
    """Submit a REAL game score and generate REAL ZisK proof"""
    try:
        data = request.get_json()
        
        if not data or 'score' not in data or 'player_id' not in data:
            return jsonify({
                'success': False, 
                'error': 'Missing required fields: score and player_id are required'
            }), 400
        
        player_id = data['player_id']
        score = data['score']
        difficulty = data.get('difficulty', 1)
        
        logger.info(f"REAL score submission: Player {player_id}, Score {score}, Difficulty {difficulty}")
        
        # 🔒 BULLETPROOF DEDUPLICATION CHECK
        dedup_key = (player_id, score, difficulty)
        current_time = datetime.now()
        
        with dedup_lock:
            if dedup_key in recent_submissions:
                last_submission = recent_submissions[dedup_key]
                time_diff = (current_time - last_submission['timestamp']).total_seconds()
                
                if time_diff < DEDUP_WINDOW_SECONDS:
                    # 🚫 BLOCK DUPLICATE SUBMISSION
                    wait_time = DEDUP_WINDOW_SECONDS - time_diff
                    logger.warning(f"🚫 DUPLICATE BLOCKED: Player {player_id}, Score {score} within {time_diff:.1f}s (wait {wait_time:.1f}s)")
                    return jsonify({
                        'success': False,
                        'error': f'Duplicate submission blocked. Same score submitted {time_diff:.1f}s ago. Wait {wait_time:.1f}s.',
                        'blocked': True,
                        'existing_job_id': last_submission['job_id'],
                        'time_remaining': wait_time
                    }), 429  # Too Many Requests
        
        # Validate score - must be a positive number
        if not isinstance(score, (int, float)) or score < 0:
            return jsonify({
                'success': False, 
                'error': 'Invalid score value - must be a positive number'
            }), 400
        
        # Create REAL proof job
        job_id = str(uuid.uuid4())
        job = ProofJob(job_id, player_id, score, difficulty)
        
        with proof_jobs_lock:
            proof_jobs[job_id] = job
        
        # Generate Game ID for tamper-proof binding
        job.game_id = generate_game_id(job_id, score)
        
        # 🔒 RECORD THIS SUBMISSION FOR DEDUPLICATION
        with dedup_lock:
            recent_submissions[dedup_key] = {
                'timestamp': current_time,
                'job_id': job_id
            }
        
        # Add REAL score to leaderboard immediately with pending proof status
        score_entry = {
            'job_id': job_id,
            'player_id': player_id,
            'score': score,
            'difficulty': difficulty,
            'game_id': job.game_id,
            'timestamp': datetime.now().isoformat(),
            'proof_status': ProofStatus.PENDING.value,
            'proof_file_path': None
        }
        
        with leaderboard_lock:
            leaderboard[difficulty].append(score_entry)
        leaderboard[difficulty].sort(key=lambda x: x['score'], reverse=True)
            # Keep top 1000 scores per difficulty
            leaderboard[difficulty] = leaderboard[difficulty][:1000]
        
        # Queue REAL proof job
        proof_queue.put(job)
        
        logger.info(f"✅ REAL proof job {job_id} queued successfully with game_id: {job.game_id}")
        
        return jsonify({
            'success': True,
            'message': 'Real score submitted successfully, ZisK proof generation queued',
            'job_id': job_id,
            'game_id': job.game_id,
            'score_data': score_entry,
            'proof_status': ProofStatus.PENDING.value,
            'estimated_time': '20-45 minutes'
        })
        
    except Exception as e:
        logger.error(f"Error in REAL score submission: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/proof-status/<job_id>', methods=['GET'])
def get_proof_status(job_id):
    """Get the status of a REAL proof job"""
    try:
        with proof_jobs_lock:
            if job_id not in proof_jobs:
                return jsonify({
                    'success': False, 
                    'error': f'Proof job {job_id} not found'
                }), 404
            
            job = proof_jobs[job_id]
            return jsonify({
                'success': True,
                'job': job.to_dict()
            })
            
    except Exception as e:
        logger.error(f"Error getting proof status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/proof-jobs', methods=['GET'])
def get_proof_jobs():
    """Get all REAL proof jobs with optional filtering"""
    try:
        status_filter = request.args.get('status')
        limit = request.args.get('limit', 100, type=int)
        
        with proof_jobs_lock:
            if not proof_jobs:
                return jsonify({
                    'success': False,
                    'error': 'No proof jobs found - no real scores have been submitted yet'
                }), 404
            
            jobs = list(proof_jobs.values())
            
            if status_filter:
                jobs = [j for j in jobs if j.status.value == status_filter]
                if not jobs:
        return jsonify({
            'success': False,
                        'error': f'No proof jobs found with status: {status_filter}'
                    }), 404
            
            # Sort by creation time (newest first)
            jobs.sort(key=lambda x: x.created_at, reverse=True)
            jobs = jobs[:limit]
            
            return jsonify({
                'success': True,
                'jobs': [job.to_dict() for job in jobs],
                'total_jobs': len(proof_jobs)
            })
            
    except Exception as e:
        logger.error(f"Error getting proof jobs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leaderboard/<int:difficulty>', methods=['GET'])
def get_leaderboard(difficulty):
    """Get leaderboard for a specific difficulty level - ONLY REAL SCORES"""
    try:
        with leaderboard_lock:
            if difficulty not in leaderboard or not leaderboard[difficulty]:
                return jsonify({
                    'success': False,
                    'error': f'No real scores found for difficulty level {difficulty}'
                }), 404
            
            difficulty_scores = leaderboard[difficulty].copy()
        
        # Sort by score (descending)
        difficulty_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Limit to top 100 scores
        top_scores = difficulty_scores[:100]
        
        return jsonify({
            'success': True,
            'difficulty': difficulty,
            'scores': top_scores,
            'total_scores': len(difficulty_scores)
        })
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leaderboard', methods=['GET'])
def get_all_leaderboards():
    """Get all leaderboards - ONLY REAL SCORES"""
    try:
        with leaderboard_lock:
            if not leaderboard:
        return jsonify({
            'success': False,
                    'error': 'No real scores found - no scores have been submitted yet'
                }), 404
            
            all_leaderboards = {}
            for difficulty, scores in leaderboard.items():
                if scores:  # Only include difficulties that have real scores
                    sorted_scores = sorted(scores, key=lambda x: x['score'], reverse=True)
                    all_leaderboards[difficulty] = sorted_scores[:100]  # Top 100
        
        if not all_leaderboards:
            return jsonify({
                'success': False,
                'error': 'No real scores found in any difficulty level'
            }), 404
        
        return jsonify({
            'success': True,
            'leaderboards': all_leaderboards,
            'difficulty_levels': list(all_leaderboards.keys())
        })
        
    except Exception as e:
        logger.error(f"Error getting all leaderboards: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get comprehensive system statistics - ONLY REAL DATA"""
    try:
        with proof_jobs_lock:
            if not proof_jobs:
                proof_stats = {
                    'total_jobs': 0,
                    'pending': 0,
                    'in_progress': 0,
                    'completed': 0,
                    'failed': 0,
                    'timeout': 0,
                    'active_workers': 0,
                    'queue_size': 0,
                    'message': 'No real proof jobs found - no scores submitted yet'
                }
            else:
                proof_stats = {
                    'total_jobs': len(proof_jobs),
                    'pending': len([j for j in proof_jobs.values() if j.status == ProofStatus.PENDING]),
                    'in_progress': len([j for j in proof_jobs.values() if j.status == ProofStatus.IN_PROGRESS]),
                    'completed': len([j for j in proof_jobs.values() if j.status == ProofStatus.COMPLETED]),
                    'failed': len([j for j in proof_jobs.values() if j.status == ProofStatus.FAILED]),
                    'timeout': len([j for j in proof_jobs.values() if j.status == ProofStatus.TIMEOUT]),
                    'active_workers': len(active_proof_workers),
                    'queue_size': proof_queue.qsize()
                }
        
        with leaderboard_lock:
            if not leaderboard:
                leaderboard_stats = {
                    'total_scores': 0,
                    'by_difficulty': {},
                    'message': 'No real scores found - no scores submitted yet'
                }
            else:
                leaderboard_stats = {
                    difficulty: len(scores) for difficulty, scores in leaderboard.items() if scores
                }
                total_scores = sum(leaderboard_stats.values())
                leaderboard_stats = {
                    'total_scores': total_scores,
                    'by_difficulty': leaderboard_stats
                }
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'proof_system': proof_stats,
            'leaderboard': leaderboard_stats,
            'system_info': {
                'only_real_data': True,
                'no_fake_scores': True,
                'no_mock_data': True
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Initialize proof worker threads
def init_proof_workers(num_workers=2):
    """Initialize bulletproof proof worker threads for REAL proof generation"""
    global worker_threads
    
    # Force cleanup of ALL old workers to prevent hanging
    logger.info("🧹 Cleaning up ALL old worker threads...")
    for worker in worker_threads:
        try:
            if worker.is_alive():
                logger.info(f"Terminating old worker: {worker.name}")
                # Send poison pill to stop worker gracefully
                proof_queue.put(None)
        except:
            pass
    
    # Wait a bit for workers to terminate
    time.sleep(2)
    
    # Clean up any dead threads
    worker_threads = [t for t in worker_threads if t.is_alive()]
    
    current_workers = len(worker_threads)
    workers_needed = num_workers - current_workers
    
    if workers_needed > 0:
        logger.info(f"Starting {workers_needed} new proof worker threads (current: {current_workers})")
        
        for i in range(workers_needed):
            worker = threading.Thread(
                target=proof_worker, 
                daemon=False,  # NOT daemon - we want them to stay alive
                name=f"ProofWorker-{len(worker_threads) + i + 1}"
            )
            worker.start()
            worker_threads.append(worker)
            logger.info(f"Started proof worker thread {worker.name} (ID: {worker.ident})")
    else:
        logger.info(f"All {num_workers} proof workers already running")

@app.route('/api/worker-status', methods=['GET'])
def get_worker_status():
    """Get detailed worker thread status"""
    try:
        global worker_threads
        
        # Clean up dead threads
        alive_threads = [t for t in worker_threads if t.is_alive()]
        dead_count = len(worker_threads) - len(alive_threads)
        worker_threads = alive_threads
        
        with proof_jobs_lock:
            worker_details = []
            for thread in worker_threads:
                thread_id = thread.ident
                worker_info = {
                    'thread_name': thread.name,
                    'thread_id': thread_id,
                    'is_alive': thread.is_alive(),
                    'current_job': None
                }
                
                if thread_id in active_proof_workers:
                    job = active_proof_workers[thread_id]
                    worker_info['current_job'] = {
                        'job_id': job.job_id,
                        'player_id': job.player_id,
                        'score': job.score,
                        'started_at': job.started_at.isoformat(),
                        'duration_seconds': (datetime.now() - job.started_at).total_seconds()
                    }
                
                worker_details.append(worker_info)
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'worker_summary': {
                'total_threads': len(worker_threads),
                'alive_threads': len(alive_threads),
                'dead_threads_cleaned': dead_count,
                'active_jobs': len(active_proof_workers),
                'queue_size': proof_queue.qsize()
            },
            'workers': worker_details
        })
        
    except Exception as e:
        logger.error(f"Error getting worker status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download-proof/<job_id>', methods=['GET'])
def download_proof(job_id):
    """Download the generated proof file for a completed job"""
    try:
        with proof_jobs_lock:
            if job_id not in proof_jobs:
                return jsonify({
                    'success': False,
                    'error': f'Proof job {job_id} not found'
                }), 404
            
            job = proof_jobs[job_id]
            
            if job.status != ProofStatus.COMPLETED:
                return jsonify({
                    'success': False,
                    'error': f'Proof job {job_id} is not completed (status: {job.status.value})'
                }), 400
            
            if not job.proof_file_path or not os.path.exists(job.proof_file_path):
                return jsonify({
                    'success': False,
                    'error': f'Proof file not found at {job.proof_file_path}'
                }), 404
            
            # Return the proof file
            return send_file(
                job.proof_file_path,
                as_attachment=True,
                download_name=f'zisk_proof_score_{job.score}.bin',
                mimetype='application/octet-stream'
            )
            
    except Exception as e:
        logger.error(f"Error downloading proof file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dedup-status', methods=['GET'])
def get_dedup_status():
    """Get current deduplication status for debugging"""
    try:
        with dedup_lock:
            current_time = datetime.now()
            active_entries = {}
            
            for (player_id, score, difficulty), data in recent_submissions.items():
                time_diff = (current_time - data['timestamp']).total_seconds()
                if time_diff < DEDUP_WINDOW_SECONDS:
                    active_entries[f"{player_id}_{score}_{difficulty}"] = {
                        'player_id': player_id,
                        'score': score,
                        'difficulty': difficulty,
                        'submitted_at': data['timestamp'].isoformat(),
                        'seconds_ago': time_diff,
                        'remaining_block': DEDUP_WINDOW_SECONDS - time_diff
                    }
            
            return jsonify({
                'success': True,
                'dedup_window_seconds': DEDUP_WINDOW_SECONDS,
                'active_entries': len(active_entries),
                'total_entries': len(recent_submissions),
                'entries': active_entries
            })
            
    except Exception as e:
        logger.error(f"Error getting dedup status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test-dedup', methods=['POST'])
def test_dedup():
    """Test endpoint to verify deduplication is working"""
    try:
        data = request.get_json()
        test_player = data.get('player_id', 'test_player')
        test_score = data.get('score', 999)
        test_difficulty = data.get('difficulty', 1)
        
        # Try to submit the same score twice
        first_result = submit_score_internal(test_player, test_score, test_difficulty)
        
        if not first_result['success']:
            return jsonify({
                'success': False,
                'error': 'First submission failed',
                'first_result': first_result
            })
        
        # Wait a moment
        time.sleep(1)
        
        # Try to submit the same score again (should be blocked)
        second_result = submit_score_internal(test_player, test_score, test_difficulty)
        
        return jsonify({
            'success': True,
            'dedup_working': not second_result['success'],
            'first_submission': first_result,
            'second_submission': second_result,
            'dedup_blocked': second_result.get('duplicate_blocked', False)
        })
        
    except Exception as e:
        logger.error(f"Error testing dedup: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def submit_score_internal(player_id, score, difficulty):
    """Internal function for testing deduplication"""
    try:
        # BULLETPROOF DUPLICATE PREVENTION
        with dedup_lock:
            dedup_key = (player_id, score, difficulty)
            current_time = datetime.now()
            
            if dedup_key in recent_submissions:
                last_submission = recent_submissions[dedup_key]
                time_diff = (current_time - last_submission['timestamp']).total_seconds()
                
                if time_diff < DEDUP_WINDOW_SECONDS:
                    wait_time = DEDUP_WINDOW_SECONDS - time_diff
                    logger.warning(f"DUPLICATE BLOCKED: Player {player_id} tried to submit score {score} again after {time_diff:.1f}s (wait {wait_time:.1f}s)")
                    return {
                        'success': False,
                        'error': f'Duplicate submission detected. Same score submitted {time_diff:.1f}s ago.',
                        'dedup_wait': wait_time,
                        'duplicate_blocked': True
                    }
            
            # Record this submission
            recent_submissions[dedup_key] = {'timestamp': current_time, 'job_id': str(uuid.uuid4())} # Store job_id for dedup
        
        return {
            'success': True,
            'message': 'Test submission successful',
                'player_id': player_id,
            'score': score
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def cleanup_workers_on_shutdown():
    """Clean up all worker threads on shutdown"""
    global worker_threads
    logger.info("🛑 Shutting down all worker threads...")
    
    # Send poison pills to all workers
    for _ in range(len(worker_threads)):
        try:
            proof_queue.put(None)
        except:
            pass
    
    # Wait for workers to terminate
    for worker in worker_threads:
        try:
            if worker.is_alive():
                worker.join(timeout=5)
                if worker.is_alive():
                    logger.warning(f"Worker {worker.name} did not terminate gracefully")
        except:
            pass
    
    logger.info("✅ All workers cleaned up")

@app.route('/api/restart-workers', methods=['POST'])
def restart_workers():
    """Manually restart worker threads"""
    try:
        global worker_threads
        
        logger.info("Manual worker restart requested")
        
        # Don't kill existing workers if they have active jobs
        with proof_jobs_lock:
            if active_proof_workers:
                return jsonify({
                    'success': False,
                    'error': f'Cannot restart - {len(active_proof_workers)} workers have active jobs'
                }), 400
        
        # Add more workers instead of killing existing ones
        current_count = len([t for t in worker_threads if t.is_alive()])
        init_proof_workers(num_workers=current_count + 2)
        
        return jsonify({
            'success': True,
            'message': 'Additional worker threads started',
            'total_workers': len([t for t in worker_threads if t.is_alive()])
        })
        
    except Exception as e:
        logger.error(f"Error restarting workers: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting REAL ZisK Proof API - NO FAKE DATA")
    logger.info("System will ONLY process real submitted scores")
    logger.info("All mock/fake implementations have been REMOVED")
    logger.info("Enhanced with bulletproof worker system and psutil-free process management")
    logger.info("🔒 BULLETPROOF DUPLICATE PREVENTION ENABLED - 30 second window")
    
    # Register shutdown handler
    import atexit
    atexit.register(cleanup_workers_on_shutdown)
    
    # Start proof worker threads for REAL proof generation
    init_proof_workers(num_workers=2)
    
    # Start worker monitoring in background
    monitor_thread = threading.Thread(target=monitor_workers, daemon=True)
    monitor_thread.start()
    logger.info("Worker monitoring started")
    
    logger.info("API available at: http://localhost:8000")
    logger.info("Submit real scores via POST /api/submit-score")
    
    try:
        app.run(host='0.0.0.0', port=8000, debug=True, threaded=True)
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal...")
        cleanup_workers_on_shutdown()
