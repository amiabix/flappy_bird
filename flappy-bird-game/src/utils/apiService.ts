const API_BASE_URL = 'http://localhost:8000';

export interface ScoreSubmission {
  player_id: string;
  score: number;
  difficulty: number;
}

export interface LeaderboardEntry {
  player_id: string;
  score: number;
  difficulty: number;
  timestamp: string;
  source: string;
  proof_hash: string;
}

export interface LeaderboardResponse {
  difficulty: number;
  scores: LeaderboardEntry[];
  total_players: number;
  background_fetcher_status: string;
}

export class ApiService {
  static async submitScore(scoreData: ScoreSubmission): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/submit-score`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(scoreData),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Score submitted successfully:', result);
        return result;
      } else {
        const errorData = await response.json();
        console.error('❌ Failed to submit score:', response.statusText);
        throw new Error(errorData.error || response.statusText);
      }
    } catch (error) {
      console.error('❌ Error submitting score:', error);
      throw error;
    }
  }

  static async getLeaderboard(difficulty: number = 1): Promise<LeaderboardResponse | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/leaderboard/${difficulty}`);
      
      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        console.error('❌ Failed to fetch leaderboard:', response.statusText);
        return null;
      }
    } catch (error) {
      console.error('❌ Error fetching leaderboard:', error);
      return null;
    }
  }

  static async getStats(): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/stats`);
      
      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        console.error('❌ Failed to fetch stats:', response.statusText);
        return null;
      }
    } catch (error) {
      console.error('❌ Error fetching stats:', error);
      return null;
    }
  }

  static generatePlayerId(): string {
    const timestamp = Date.now();
    const random = Math.floor(Math.random() * 10000);
    return 'player_' + timestamp + '_' + random;
  }
}
