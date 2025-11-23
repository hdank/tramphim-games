// API base URL - update for production
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002';

class GameAPI {
    async getGameConfig() {
        const response = await fetch(`${API_BASE_URL}/game/config`);
        if (!response.ok) throw new Error('Failed to get config');
        return response.json();
    }

    async startGame(playerEmail, levelId) {
        const response = await fetch(`${API_BASE_URL}/game/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player_email: playerEmail, level_id: levelId }),
        });
        if (!response.ok) throw new Error('Failed to start game');
        return response.json();
    }

    async getGame(matchId) {
        const response = await fetch(`${API_BASE_URL}/game/${matchId}`);
        if (!response.ok) throw new Error('Failed to get game');
        return response.json();
    }

    async flipCard(matchId, cardIndex1, cardIndex2) {
        const response = await fetch(`${API_BASE_URL}/game/${matchId}/flip`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ card_index_1: cardIndex1, card_index_2: cardIndex2 }),
        });

        const data = await response.json();

        if (!response.ok) {
            const error = new Error(data.detail || 'Failed to flip card');
            error.response = { status: response.status, data };
            throw error;
        }

        return data;
    }

    async giveUp(matchId) {
        // Use keepalive to ensure request completes even if page unloads
        const response = await fetch(`${API_BASE_URL}/game/${matchId}/give-up`, {
            method: 'POST',
            keepalive: true,
        });
        if (!response.ok) throw new Error('Failed to give up');
        return response.json();
    }

    async getUserPoints(email) {
        // Fetch user points from tramphim-backend
        const tramphimUrl = import.meta.env.VITE_TRAMPHIM_API_URL || 'http://localhost:8003';
        const response = await fetch(`${tramphimUrl}/api/minigame/points?email=${encodeURIComponent(email)}`);
        if (!response.ok) throw new Error('Failed to get user points');
        return response.json();
    }
}

export default new GameAPI();
