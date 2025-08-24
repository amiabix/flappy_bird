from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import threading
import time
from datetime import datetime
import uuid
import queue
import logging
from collections import defaultdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

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

# Thread synchronization
leaderboard_lock = threading.RLock()
proof_jobs_lock = threading.RLock()

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
        
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'player_id': self.player_id,
            'score': self.score,
            'difficulty': self.difficulty,
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
    """Worker thread that processes real proof generation jobs"""
    thread_id = threading.get_ident()
    logger.info(f"Proof worker {thread_id} started")
    
    while True:
        try:
            # Get next REAL job from queue (blocks until available)
            job = proof_queue.get(timeout=30)
            if job is None:  # Poison pill to stop worker
                break
                
            logger.info(f"Worker {thread_id} processing REAL proof job {job.job_id}")
            
            with proof_jobs_lock:
                active_proof_workers[thread_id] = job
                job.status = ProofStatus.IN_PROGRESS
                job.started_at = datetime.now()
                proof_jobs[job.job_id] = job
            
            # Generate the REAL ZisK proof
            result = generate_real_zisk_proof(job)
            
            with proof_jobs_lock:
                if result['success']:
                    job.status = ProofStatus.COMPLETED
                    job.proof_output = result.get('output')
                    job.proof_file_path = result.get('proof_file_path')
                else:
                    job.status = ProofStatus.FAILED
                    job.error_message = result.get('error')
                
                job.completed_at = datetime.now()
                proof_jobs[job.job_id] = job
                
                # Remove from active workers
                if thread_id in active_proof_workers:
                    del active_proof_workers[thread_id]
            
            # Update leaderboard with REAL proof result
            update_leaderboard_with_real_proof(job)
            
            logger.info(f"Worker {thread_id} completed REAL proof job {job.job_id} with status {job.status.value}")
            
        except queue.Empty:
            continue  # No jobs available, keep waiting
        except Exception as e:
            logger.error(f"Proof worker {thread_id} error: {e}")
            if 'job' in locals():
                with proof_jobs_lock:
                    job.status = ProofStatus.FAILED
                    job.error_message = str(e)
                    job.completed_at = datetime.now()
                    if thread_id in active_proof_workers:
                        del active_proof_workers[thread_id]
        finally:
            if 'job' in locals():
                proof_queue.task_done()
    
    logger.info(f"Proof worker {thread_id} stopped")

def generate_real_zisk_proof(job):
    """Generate REAL ZisK proof using the actual script - NO FAKES"""
    try:
        logger.info(f"Starting REAL ZisK proof generation for job {job.job_id}, score: {job.score}")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, "generate_zk_proof_fixed.sh")
        
        if not os.path.exists(script_path):
            return {
                "success": False,
                "error": f"ZisK proof script not found at {script_path}"
            }
        
        logger.info(f"Running REAL ZisK script: {script_path} {job.score}")
        
        # Call the REAL enhanced ZisK script
        process = subprocess.Popen(
            [script_path, str(job.score)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=current_dir,
            preexec_fn=os.setsid  # Create new process group for cleanup
        )
        
        # Store PID for potential cleanup
        with proof_jobs_lock:
            job.process_pid = process.pid
        
        try:
            # Wait for REAL proof completion with proper timeout (45 minutes)
            stdout, stderr = process.communicate(timeout=2700)
            
            logger.info(f"REAL ZisK script completed for job {job.job_id} with exit code: {process.returncode}")
            
            if process.returncode == 0:
                # Check if REAL proof file was generated
                proof_dir = os.path.join(current_dir, "flappy_zisk", "proof")
                proof_file = os.path.join(proof_dir, "vadcop_final_proof.bin")
                
                if os.path.exists(proof_file) and os.path.getsize(proof_file) > 0:
                    return {
                        "success": True,
                        "output": stdout,
                        "proof_file_path": proof_file
                    }
                else:
                    return {
                        "success": False,
                        "error": "ZisK proof file was not generated or is empty",
                        "output": stdout
                    }
            else:
                return {
                    "success": False,
                    "error": stderr or "ZisK proof generation failed",
                    "output": stdout
                }
                
        except subprocess.TimeoutExpired:
            logger.warning(f"REAL ZisK proof generation timeout for job {job.job_id}")
            
            # Kill the process group
            try:
                os.killpg(os.getpgid(process.pid), 9)
            except:
                pass
            
            with proof_jobs_lock:
                job.status = ProofStatus.TIMEOUT
            
            return {
                "success": False,
                "error": "REAL ZisK proof generation timed out after 45 minutes"
            }
            
    except Exception as e:
        logger.error(f"Error in REAL ZisK proof generation for job {job.job_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

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
        
        # Add REAL score to leaderboard immediately with pending proof status
        score_entry = {
            'job_id': job_id,
            'player_id': player_id,
            'score': score,
            'difficulty': difficulty,
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
        
        logger.info(f"REAL proof job {job_id} queued successfully")
        
        return jsonify({
            'success': True,
            'message': 'Real score submitted successfully, ZisK proof generation queued',
            'job_id': job_id,
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
    """Initialize proof worker threads for REAL proof generation"""
    for i in range(num_workers):
        worker = threading.Thread(target=proof_worker, daemon=True)
        worker.start()
        logger.info(f"Started REAL proof worker thread {worker.ident}")

if __name__ == '__main__':
    logger.info("Starting REAL ZisK Proof API - NO FAKE DATA")
    logger.info("System will ONLY process real submitted scores")
    logger.info("All mock/fake implementations have been REMOVED")
    
    # Start proof worker threads for REAL proof generation
    init_proof_workers(num_workers=2)
    
    logger.info("API available at: http://localhost:8000")
    logger.info("Submit real scores via POST /api/submit-score")
    
    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True)
