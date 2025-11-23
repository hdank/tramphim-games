import React, { useState, useEffect, useRef } from 'react';
import Card from './Card';
import gameAPI from '../api';
import vi from '../lang/vi';
import './GameBoard.css';

const GameBoard = () => {
    const [gameId, setGameId] = useState(null);
    const [game, setGame] = useState(null);
    const [playerEmail, setPlayerEmail] = useState('');
    const [levelId, setLevelId] = useState(null);
    const [isStarted, setIsStarted] = useState(false);
    const [isFlipping, setIsFlipping] = useState(false);
    const [message, setMessage] = useState('');
    const [loading, setLoading] = useState(false);
    const [timeLeft, setTimeLeft] = useState(0);
    const [showTimeWarning, setShowTimeWarning] = useState(false);
    const [flipDuration, setFlipDuration] = useState(0.6);
    const [consecutiveWins, setConsecutiveWins] = useState(0);

    // Use refs for values needed in cleanup/event listeners
    const gameIdRef = useRef(null);
    const isGameActiveRef = useRef(false);
    const lastServerTimeRef = useRef(null);
    const localCountdownStartRef = useRef(null);
    const isCreatingGameRef = useRef(false); // Prevent duplicate game creation

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const emailParam = params.get('email');
        const levelParam = params.get('level_id');

        if (emailParam) setPlayerEmail(emailParam);
        if (levelParam) setLevelId(parseInt(levelParam));

        // Only start game if not already creating/started
        if (emailParam && levelParam && !isCreatingGameRef.current && !isGameActiveRef.current) {
            autoStartGame(emailParam, parseInt(levelParam));
        }

        // Anti-cheat: Handle page unload/reload
        const handleBeforeUnload = (e) => {
            if (isGameActiveRef.current) {
                // Standard way to show confirmation dialog
                e.preventDefault();
                e.returnValue = '';
                return '';
            }
        };

        const handleUnload = () => {
            if (isGameActiveRef.current && gameIdRef.current) {
                // Call give-up endpoint using keepalive
                gameAPI.giveUp(gameIdRef.current).catch(err => console.error("Failed to send give-up signal", err));
            }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        window.addEventListener('unload', handleUnload);

        return () => {
            window.removeEventListener('beforeunload', handleBeforeUnload);
            window.removeEventListener('unload', handleUnload);
        };
    }, []);

    useEffect(() => {
        if (!game || !isStarted || game.status !== 'PLAYING') return;

        // Use server's time_remaining if available, or calculate from created_at
        const initializeTimer = () => {
            if (game.time_remaining !== null && game.time_remaining !== undefined) {
                // Server sent us the remaining time
                setTimeLeft(game.time_remaining);
                lastServerTimeRef.current = game.time_remaining;
                localCountdownStartRef.current = Date.now();
            } else if (game.level && game.created_at) {
                // Fallback: Calculate from created_at
                const now = Date.now();
                const elapsed = Math.floor((now - new Date(game.created_at).getTime()) / 1000);

                if (game.level.time_limit) {
                    const remaining = Math.max(0, game.level.time_limit - elapsed);
                    setTimeLeft(remaining);
                    lastServerTimeRef.current = remaining;
                    localCountdownStartRef.current = Date.now();
                } else {
                    setTimeLeft(elapsed);
                }
            }
        };

        initializeTimer();

        // Update timer every 100ms for smooth countdown
        const timer = setInterval(() => {
            if (lastServerTimeRef.current !== null && localCountdownStartRef.current !== null) {
                const elapsedLocal = (Date.now() - localCountdownStartRef.current) / 1000;
                const remaining = Math.max(0, lastServerTimeRef.current - elapsedLocal);

                setTimeLeft(Math.ceil(remaining)); // Ceil to avoid going negative in display

                // Show warning when time is running low (< 10 seconds)
                if (remaining <= 10 && remaining > 0) {
                    setShowTimeWarning(true);
                } else {
                    setShowTimeWarning(false);
                }

                // Auto-fail if time runs out (in case server doesn't catch it)
                if (remaining <= 0) {
                    setGame({ ...game, status: 'LOSE' });
                    setMessage("Hết giờ!");
                    isGameActiveRef.current = false;
                    clearInterval(timer);
                }
            }
        }, 100);

        return () => clearInterval(timer);
    }, [game, isStarted]);

    const refreshPoints = () => {
        setTimeout(async () => {
            try {
                const pointsData = await gameAPI.getUserPoints(playerEmail);
                window.parent.postMessage({
                    type: 'POINTS_UPDATED',
                    points: pointsData.points
                }, '*');
            } catch (err) {
                console.error('Failed to refresh points:', err);
            }
        }, 2000);
    };

    const getWinBonus = (wins) => {
        return wins > 1 ? 2 : 1;
    };

    const autoStartGame = async (email, level) => {
        // Prevent duplicate game creation
        if (isCreatingGameRef.current) {
            console.log('Game creation already in progress, skipping...');
            return;
        }

        isCreatingGameRef.current = true;

        try {
            setLoading(true);
            const gameData = await gameAPI.startGame(email, level);
            setGameId(gameData.id);
            gameIdRef.current = gameData.id;
            setGame(gameData);
            setIsStarted(true);
            isGameActiveRef.current = true;
            setMessage('');

            // Apply difficulty bonus from backend (affects flip-back duration)
            if (gameData.flip_duration !== null && gameData.flip_duration !== undefined) {
                setFlipDuration(gameData.flip_duration);
                // Use server-provided consecutive_wins
                setConsecutiveWins(gameData.consecutive_wins || 0);
            }

            // Initialize timer with server's time_remaining
            if (gameData.time_remaining !== null && gameData.time_remaining !== undefined) {
                setTimeLeft(gameData.time_remaining);
                lastServerTimeRef.current = gameData.time_remaining;
                localCountdownStartRef.current = Date.now();
            } else if (gameData.level?.time_limit) {
                const elapsed = Math.floor((Date.now() - new Date(gameData.created_at).getTime()) / 1000);
                const remaining = Math.max(0, gameData.level.time_limit - elapsed);
                setTimeLeft(remaining);
                lastServerTimeRef.current = remaining;
                localCountdownStartRef.current = Date.now();
            } else {
                setTimeLeft(0);
            }
        } catch (error) {
            console.error('Failed to start game:', error);
            setMessage(vi.failedToStart || "Không thể bắt đầu game");
            isCreatingGameRef.current = false; // Reset on error
        } finally {
            setLoading(false);
        }
    };

    const handleCardFlip = async (cardIndex) => {
        if (isFlipping || !gameId || game.status !== 'PLAYING') {
            return;
        }

        // Immediately flip the card on frontend
        const newCardsState = game.cards_state.map((card, idx) => {
            if (idx === cardIndex) {
                return { ...card, flipped: true };
            }
            return card;
        });

        const newFlippedIndices = [...(game.flipped_indices || []), cardIndex];

        setGame({
            ...game,
            cards_state: newCardsState,
            flipped_indices: newFlippedIndices
        });

        // Only send to backend when 2 cards are flipped
        if (newFlippedIndices.length === 2) {
            setIsFlipping(true);

            try {
                const response = await gameAPI.flipCard(gameId, newFlippedIndices[0], newFlippedIndices[1]);
                const updatedGame = response.match;

                // Resync timer with server's time_remaining
                if (updatedGame.time_remaining !== null && updatedGame.time_remaining !== undefined) {
                    lastServerTimeRef.current = updatedGame.time_remaining;
                    localCountdownStartRef.current = Date.now();
                    setTimeLeft(updatedGame.time_remaining);
                }

                let translatedMessage = response.message;
                if (response.is_match === true) {

                    // Update with matched cards from backend
                    setGame({
                        ...updatedGame,
                        cards_state: updatedGame.cards_state,
                        flipped_indices: []
                    });

                    if (updatedGame.status === 'WIN') {
                        translatedMessage = vi.gameComplete || "Bạn đã thắng!";
                        isGameActiveRef.current = false;
                        isCreatingGameRef.current = false; // Allow new game creation
                        // Increment consecutive wins on victory
                        setConsecutiveWins(prev => prev + 1);
                        window.parent.postMessage({ type: 'GAME_COMPLETE', score: updatedGame.score }, '*');
                        refreshPoints();
                    }

                    setIsFlipping(false);
                } else if (response.is_match === false) {
                    translatedMessage = vi.noMatch || "Không khớp";

                    // Wait a moment then flip them back
                    // Use server-provided flip duration (converted to ms)
                    const flipBackDelay = (updatedGame.flip_duration || 0.6) * 1000;

                    setTimeout(() => {
                        setGame({
                            ...updatedGame,
                            cards_state: updatedGame.cards_state,
                            flipped_indices: []
                        });
                        setIsFlipping(false);
                    }, flipBackDelay);
                } else if (updatedGame.status === 'LOSE') {
                    translatedMessage = "Trò chơi kết thúc";
                    isGameActiveRef.current = false;
                    isCreatingGameRef.current = false; // Allow new game creation
                    setGame({
                        ...updatedGame,
                        cards_state: updatedGame.cards_state,
                        flipped_indices: []
                    });
                    setIsFlipping(false);
                    refreshPoints();
                }

                setMessage(translatedMessage);
            } catch (error) {
                console.error('Failed to check match:', error);

                // Server returned timeout error
                if (error.response?.status === 400 && error.response?.data?.detail === "Time limit exceeded") {
                    setGame({ ...game, status: 'LOSE' });
                    setMessage("Hết giờ!");
                    isGameActiveRef.current = false;
                    isCreatingGameRef.current = false; // Allow new game creation
                    refreshPoints();
                }

                setIsFlipping(false);
            }
        }
    };

    const handleBackToGame = () => {
        window.parent.postMessage({ type: 'NAVIGATE_BACK' }, '*');
    };

    if (!isStarted) {
        return (
            <div className="h-full w-full flex items-center justify-center">
                <div className="text-center glass-panel p-8 rounded-2xl">
                    <div className="spinner mb-4 mx-auto"></div>
                    <p className="text-gray-300 font-medium">Đang tải trò chơi...</p>
                </div>
            </div>
        );
    }

    if (!game) return null;

    // Calculate grid columns based on card count and viewport
    const totalCards = game.cards_state.length;
    let gridCols = 'grid-cols-3';
    let gapSize = 'gap-1';
    let padding = 'p-1';

    // Adjust for larger screen sizes and LOW card counts
    if (totalCards <= 8) {
        // For very few cards, use fewer columns to make them bigger
        gridCols = 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4';
        gapSize = 'gap-2 sm:gap-3 lg:gap-4';
        padding = 'p-4 sm:p-6 lg:p-8';
    } else if (totalCards <= 16) {
        gridCols = 'grid-cols-4 sm:grid-cols-5 lg:grid-cols-6';
        gapSize = 'gap-1 sm:gap-2 lg:gap-3';
        padding = 'p-1 sm:p-2 lg:p-4';
    } else if (totalCards <= 24) {
        gridCols = 'grid-cols-4 sm:grid-cols-5 lg:grid-cols-6';
        gapSize = 'gap-1 sm:gap-2 lg:gap-2';
        padding = 'p-1 sm:p-2 lg:p-3';
    } else {
        gridCols = 'grid-cols-5 sm:grid-cols-6 lg:grid-cols-8';
        gapSize = 'gap-1 sm:gap-1 lg:gap-2';
        padding = 'p-1 sm:p-1 lg:p-2';
    }

    return (
        <div className="h-full w-full flex flex-col overflow-hidden font-sans relative">
            {/* Header - Glassmorphism */}
            <div className="flex-none glass z-20 px-4 py-3 flex justify-between items-center shadow-lg mx-2 mt-2 rounded-xl">
                <div className="flex items-center gap-6">
                    <div className="flex flex-col">
                        <span className="text-[10px] text-sky-300 uppercase tracking-wider font-bold">Điểm</span>
                        <span className="text-2xl font-bold text-white leading-none drop-shadow-md">{game.score}</span>
                    </div>
                    <div className="flex flex-col">
                        <span className="text-[10px] text-indigo-300 uppercase tracking-wider font-bold">Lượt</span>
                        <span className="text-2xl font-bold text-white leading-none drop-shadow-md">{game.moves}</span>
                    </div>
                </div>
                <div className="flex flex-col items-end">
                    <span className="text-[10px] text-amber-300 uppercase tracking-wider font-bold">Thời gian</span>
                    <span className={`text-2xl font-mono font-bold leading-none drop-shadow-md transition-colors ${showTimeWarning ? 'text-red-400 animate-pulse' : timeLeft <= 0 ? 'text-red-500' : 'text-white'}`}>
                        {Math.floor(timeLeft / 60)}:{String(timeLeft % 60).padStart(2, '0')}
                    </span>
                </div>
            </div>

            {/* Game Area - Responsive Grid */}
            <div className="flex-1 overflow-y-auto p-2 sm:p-4 flex items-center justify-center">
                <div className="w-full max-w-6xl mx-auto h-full flex flex-col justify-center">
                    <div className={`grid ${gridCols} ${gapSize} auto-rows-fr w-full h-full max-h-[85vh] ${padding}`}>
                        {game.cards_state.map((card, index) => (
                            <div key={index} className="w-full h-full relative" style={{ aspectRatio: '3/4', visibility: card.matched ? 'hidden' : 'visible' }}>
                                <Card
                                    card={card}
                                    index={index}
                                    onFlip={handleCardFlip}
                                    disabled={isFlipping || game.status !== 'PLAYING' || card.matched}
                                    flipDuration={flipDuration}
                                />
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Game Over / Victory Modal */}
            {game.status !== 'PLAYING' && (
                <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-md flex items-center justify-center p-4 animate-fade-in">
                    <div className="glass-panel p-8 rounded-3xl text-center max-w-sm w-full transform scale-100 transition-transform animate-scale-in border border-white/10">
                        <div className="mb-6 relative">
                            <div className={`absolute inset-0 blur-xl opacity-50 ${game.status === 'WIN' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                            {game.status === 'WIN' ? (
                                <div className="w-24 h-24 bg-gradient-to-br from-green-400 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4 relative z-10 shadow-lg shadow-green-500/30">
                                    <span className="text-5xl animate-bounce-slow">🏆</span>
                                </div>
                            ) : (
                                <div className="w-24 h-24 bg-gradient-to-br from-red-400 to-rose-600 rounded-full flex items-center justify-center mx-auto mb-4 relative z-10 shadow-lg shadow-red-500/30">
                                    <span className="text-5xl">💀</span>
                                </div>
                            )}
                            <h2 className={`text-4xl font-bold mb-2 text-transparent bg-clip-text ${game.status === 'WIN' ? 'bg-gradient-to-r from-green-300 to-emerald-300' : 'bg-gradient-to-r from-red-300 to-rose-300'}`}>
                                {game.status === 'WIN' ? 'Chiến Thắng!' : 'Thất Bại'}
                            </h2>
                            <p className="text-gray-300 font-medium">
                                {game.status === 'WIN' ? 'Bạn đã tìm thấy tất cả các cặp!' : 'Chúc bạn may mắn lần sau.'}
                            </p>

                            {game.level && (
                                <div className="flex flex-col gap-2 justify-center mt-4">
                                    {game.status === 'WIN' ? (
                                        <>
                                            {/* For WIN: Show points from backend */}
                                            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-green-500/20 text-green-300 border border-green-500/30">
                                                <span className="text-lg font-bold">+{game.points_change || (game.level.points_reward * getWinBonus(game.consecutive_wins))} Đậu</span>
                                            </div>
                                            {/* Show NEXT game's bonus (consecutive_wins + 1) */}
                                            {(game.consecutive_wins + 1) > 1 && (
                                                <div className="text-xs text-yellow-300 font-medium">Thưởng x{getWinBonus(game.consecutive_wins + 1)} (Trò chơi tiếp theo)</div>
                                            )}
                                        </>
                                    ) : (
                                        <>
                                            {/* For LOSS: Show penalty from backend */}
                                            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/20 text-red-300 border border-red-500/30">
                                                <span className="text-lg font-bold">{game.points_change || (-game.level.points_penalty * getWinBonus(game.consecutive_wins))} Đậu</span>
                                            </div>
                                            {game.consecutive_wins > 1 && (
                                                <div className="text-xs text-yellow-300 font-medium">Phạt x{getWinBonus(game.consecutive_wins)} (Từ chiến thắng liên tiếp)</div>
                                            )}
                                        </>
                                    )}
                                </div>
                            )}
                        </div>

                        <div className="grid grid-cols-2 gap-4 mb-8">
                            <div className="bg-white/5 p-4 rounded-2xl border border-white/10">
                                <div className="text-xs text-gray-400 uppercase tracking-wider font-bold mb-1">Điểm số</div>
                                <div className="text-2xl font-bold text-white">{game.score}</div>
                            </div>
                            <div className="bg-white/5 p-4 rounded-2xl border border-white/10">
                                <div className="text-xs text-gray-400 uppercase tracking-wider font-bold mb-1">Thời gian</div>
                                <div className="text-2xl font-bold text-white">{Math.floor(timeLeft / 60)}:{String(timeLeft % 60).padStart(2, '0')}</div>
                            </div>
                        </div>

                        <div className="flex flex-col gap-3">
                            <button
                                onClick={() => window.location.reload()}
                                className="w-full py-4 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white rounded-xl font-bold text-lg transition-all shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 transform hover:-translate-y-1 flex items-center justify-center gap-2"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" /><path d="M3 3v5h5" /></svg>
                                Tiếp tục
                            </button>

                            <button
                                onClick={handleBackToGame}
                                className="w-full py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 border border-white/10"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
                                Quay lại trang trò chơi
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default GameBoard;
