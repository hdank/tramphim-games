import React, { useState, useEffect } from 'react';
import gameAPI from '../api';
import vi from '../lang/vi';
import './AdminPanel.css';

const AdminPanel = () => {
    const [stats, setStats] = useState(null);
    const [leaderboard, setLeaderboard] = useState([]);
    const [settings, setSettings] = useState(null);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState('');
    const [webhookTesting, setWebhookTesting] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [statsData, leaderboardData, settingsData] = await Promise.all([
                gameAPI.getAdminStats(),
                gameAPI.getLeaderboard(),
                gameAPI.getSettings(),
            ]);
            setStats(statsData);
            setLeaderboard(leaderboardData);
            setSettings(settingsData);
        } catch (error) {
            console.error('Failed to load admin data:', error);
            setMessage(vi.failedToLoad);
        } finally {
            setLoading(false);
        }
    };

    const handleSettingsUpdate = async (e) => {
        e.preventDefault();
        try {
            await gameAPI.updateSettings(settings);
            setMessage(vi.settingsUpdated);
            setTimeout(() => setMessage(''), 3000);
        } catch (error) {
            console.error('Failed to update settings:', error);
            setMessage(vi.failedToLoad);
        }
    };

    const testWebhook = async () => {
        try {
            setWebhookTesting(true);
            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/admin/test-webhook`, {
                method: 'POST',
            });
            const result = await response.json();

            if (result.success) {
                setMessage(vi.webhookSuccess);
            } else {
                setMessage(vi.webhookFailed + result.message);
            }
            setTimeout(() => setMessage(''), 5000);
        } catch (error) {
            console.error('Webhook test failed:', error);
            setMessage(vi.webhookFailed + error.message);
        } finally {
            setWebhookTesting(false);
        }
    };

    const updateSetting = (key, value) => {
        setSettings({ ...settings, [key]: value });
    };

    if (loading) {
        return (
            <div className="admin-container">
                <div className="spinner"></div>
            </div>
        );
    }

    return (
        <div className="admin-container fade-in">
            <div className="admin-header">
                <h1>{vi.adminDashboard}</h1>
                <button className="btn btn-secondary" onClick={loadData}>
                    {vi.refreshData}
                </button>
            </div>

            {message && <div className="message success">{message}</div>}

            {/* Statistics Overview */}
            <div className="admin-grid">
                <div className="glass-card stat-card">
                    <div className="stat-icon">🎮</div>
                    <div className="stat-info">
                        <h3>{stats.total_games}</h3>
                        <p>{vi.totalGames}</p>
                    </div>
                </div>
                <div className="glass-card stat-card">
                    <div className="stat-icon">👥</div>
                    <div className="stat-info">
                        <h3>{stats.total_players}</h3>
                        <p>{vi.totalPlayers}</p>
                    </div>
                </div>
                <div className="glass-card stat-card">
                    <div className="stat-icon">⭐</div>
                    <div className="stat-info">
                        <h3>{Math.round(stats.avg_score)}</h3>
                        <p>{vi.avgScore}</p>
                    </div>
                </div>
                <div className="glass-card stat-card">
                    <div className="stat-icon">🎲</div>
                    <div className="stat-info">
                        <h3>{Math.round(stats.avg_moves)}</h3>
                        <p>{vi.avgMoves}</p>
                    </div>
                </div>
            </div>

            <div className="admin-columns">
                {/* Game Settings */}
                <div className="glass-card settings-card">
                    <h2>{vi.gameSettings}</h2>
                    <form onSubmit={handleSettingsUpdate} className="settings-form">
                        <div className="form-group">
                            <label>{vi.numPairs}</label>
                            <input
                                type="number"
                                className="input"
                                min="2"
                                max="16"
                                value={settings.num_pairs}
                                onChange={(e) => updateSetting('num_pairs', parseInt(e.target.value))}
                            />
                        </div>
                        <div className="form-group">
                            <label>{vi.timeLimit}</label>
                            <input
                                type="number"
                                className="input"
                                min="0"
                                value={settings.time_limit || 0}
                                onChange={(e) => updateSetting('time_limit', parseInt(e.target.value) || null)}
                            />
                        </div>
                        <div className="form-group">
                            <label>{vi.matchPoints}</label>
                            <input
                                type="number"
                                className="input"
                                min="1"
                                value={settings.match_points}
                                onChange={(e) => updateSetting('match_points', parseInt(e.target.value))}
                            />
                        </div>
                        <div className="form-group">
                            <label>{vi.mismatchPenalty}</label>
                            <input
                                type="number"
                                className="input"
                                min="0"
                                value={settings.mismatch_penalty}
                                onChange={(e) => updateSetting('mismatch_penalty', parseInt(e.target.value))}
                            />
                        </div>
                        <div className="form-group checkbox">
                            <label>
                                <input
                                    type="checkbox"
                                    checked={settings.time_bonus_enabled}
                                    onChange={(e) => updateSetting('time_bonus_enabled', e.target.checked)}
                                />
                                {vi.timeBonusEnabled}
                            </label>
                        </div>

                        <hr style={{ margin: '1.5rem 0', border: 0, borderTop: '1px solid var(--border-color)' }} />

                        {/* Webhook Configuration */}
                        <h3 style={{ marginBottom: '1rem' }}>{vi.webhookConfig}</h3>

                        <div className="form-group">
                            <label>{vi.webhookUrl}</label>
                            <input
                                type="url"
                                className="input"
                                placeholder="https://tramphim.com/api/minigame/game-result"
                                value={settings.webhook_url || ''}
                                onChange={(e) => updateSetting('webhook_url', e.target.value)}
                            />
                        </div>
                        <div className="form-group">
                            <label>{vi.webhookSecret}</label>
                            <input
                                type="password"
                                className="input"
                                placeholder="your-secret-key"
                                value={settings.webhook_secret || ''}
                                onChange={(e) => updateSetting('webhook_secret', e.target.value)}
                            />
                        </div>
                        <div className="form-group">
                            <label>{vi.pointsPerWin}</label>
                            <input
                                type="number"
                                className="input"
                                min="0"
                                value={settings.points_per_win}
                                onChange={(e) => updateSetting('points_per_win', parseInt(e.target.value))}
                            />
                        </div>
                        <div className="form-group">
                            <label>{vi.pointsPerLoss}</label>
                            <input
                                type="number"
                                className="input"
                                min="0"
                                value={settings.points_per_loss}
                                onChange={(e) => updateSetting('points_per_loss', parseInt(e.target.value))}
                            />
                        </div>

                        <div className="button-group" style={{ display: 'flex', gap: '0.5rem' }}>
                            <button type="submit" className="btn btn-primary">
                                {vi.saveSettings}
                            </button>
                            <button
                                type="button"
                                className="btn btn-secondary"
                                onClick={testWebhook}
                                disabled={webhookTesting || !settings.webhook_url}
                            >
                                {webhookTesting ? vi.webhookTesting : vi.testWebhook}
                            </button>
                        </div>
                    </form>
                </div>

                {/* Leaderboard */}
                <div className="glass-card leaderboard-card">
                    <h2>{vi.leaderboard}</h2>
                    <div className="leaderboard">
                        {leaderboard.length === 0 ? (
                            <p className="empty-state">{vi.noPlayers}</p>
                        ) : (
                            leaderboard.map((player, index) => (
                                <div key={index} className="leaderboard-item">
                                    <div className="rank">#{index + 1}</div>
                                    <div className="player-info">
                                        <div className="player-name">{player.player_email || vi.anonymous}</div>
                                        <div className="player-stats">
                                            {player.total_games} {vi.games} • {player.best_time ? `${player.best_time.toFixed(1)}${vi.seconds}` : 'N/A'}
                                        </div>
                                    </div>
                                    <div className="player-score">{player.best_score}</div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            {/* Best Scores */}
            <div className="glass-card">
                <h2>{vi.bestScores}</h2>
                <div className="best-scores">
                    {stats.best_scores.length === 0 ? (
                        <p className="empty-state">{vi.noGames}</p>
                    ) : (
                        <table className="scores-table">
                            <thead>
                                <tr>
                                    <th>{vi.player}</th>
                                    <th>{vi.bestScore}</th>
                                    <th>{vi.moves}</th>
                                    <th>{vi.time}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {stats.best_scores.map((score, index) => (
                                    <tr key={index}>
                                        <td>{score.player_name || vi.anonymous}</td>
                                        <td className="score-value">{score.score}</td>
                                        <td>{score.moves}</td>
                                        <td>{score.time ? `${score.time.toFixed(1)}s` : 'N/A'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AdminPanel;
