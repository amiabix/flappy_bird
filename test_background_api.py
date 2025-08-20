#!/usr/bin/env python3
"""
Test script for the Background Score Fetching API
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("🏥 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_start_background_fetcher():
    """Start the background score fetcher"""
    print("🔄 Starting background score fetcher...")
    response = requests.post(f"{BASE_URL}/api/start-background-fetcher")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_background_status():
    """Check background fetcher status"""
    print("📊 Checking background fetcher status...")
    response = requests.get(f"{BASE_URL}/api/background-status")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_get_background_scores():
    """Get background scores"""
    print("📈 Getting background scores...")
    response = requests.get(f"{BASE_URL}/api/background-scores")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_submit_manual_score():
    """Submit a manual score"""
    print("🎮 Submitting manual score...")
    score_data = {
        "player_id": "test_player_manual",
        "score": 85,
        "difficulty": 1
    }
    response = requests.post(f"{BASE_URL}/api/submit-score", json=score_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_get_stats():
    """Get overall statistics"""
    print("📊 Getting overall stats...")
    response = requests.get(f"{BASE_URL}/api/stats")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_get_leaderboard():
    """Get leaderboard"""
    print("🏆 Getting leaderboard...")
    response = requests.get(f"{BASE_URL}/api/leaderboard/1")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_stop_background_fetcher():
    """Stop the background score fetcher"""
    print("🛑 Stopping background score fetcher...")
    response = requests.post(f"{BASE_URL}/api/stop-background-fetcher")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def main():
    """Run all tests"""
    print("🧪 Testing Background Score Fetching API")
    print("=" * 50)
    
    try:
        # Test basic functionality
        test_health()
        
        # Test background fetcher
        test_start_background_fetcher()
        time.sleep(2)  # Wait a bit for fetcher to start
        
        test_background_status()
        
        # Submit a manual score
        test_submit_manual_score()
        
        # Wait for background fetcher to collect some scores
        print("⏳ Waiting 35 seconds for background fetcher to collect scores...")
        time.sleep(35)
        
        # Check results
        test_get_background_scores()
        test_get_stats()
        test_get_leaderboard()
        
        # Stop background fetcher
        test_stop_background_fetcher()
        test_background_status()
        
        print("✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server.")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    main()
