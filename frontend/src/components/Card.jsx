import React from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL;

const Card = ({ card, index, onFlip, disabled, flipDuration = 0.6 }) => {
    const handleClick = () => {
        if (!disabled && !card.flipped && !card.matched) {
            onFlip(index);
        }
    };

    const getImageUrl = (url) => {
        if (!url) return '';
        if (url.startsWith('http')) return url;
        if (url.startsWith('/static')) return `${API_BASE_URL}${url}`;
        return url;
    };

    return (
        <div
            className={`card-container w-full h-full ${card.flipped || card.matched ? 'flipped' : ''} ${card.matched ? 'matched' : ''}`}
            onClick={handleClick}
            style={{ '--flip-duration': `${flipDuration}s` }}
        >
            <div className="card-inner">
                <div className="card-front glass">
                    <div className="card-pattern opacity-30"></div>
                </div>
                <div className="card-back glass-panel">
                    {card.type === 'image' ? (
                        <img
                            src={getImageUrl(card.value)}
                            alt="card"
                            className="card-image"
                            onError={(e) => {
                                e.target.onerror = null;
                                e.target.src = 'https://via.placeholder.com/150?text=Error';
                            }}
                        />
                    ) : (
                        <span className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-br from-primary to-secondary select-none">
                            {card.value}
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Card;
