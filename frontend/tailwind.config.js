/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: '#0ea5e9',
                secondary: '#6366f1',
                dark: '#0f172a',
                surface: '#1e293b',
            },
            animation: {
                'fade-in': 'fadeIn 0.4s ease-out',
                'scale-in': 'scaleIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                'bounce-slow': 'bounce 3s infinite',
                'pulse-glow': 'pulseGlow 2s infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0', transform: 'translateY(10px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                scaleIn: {
                    '0%': { opacity: '0', transform: 'scale(0.9)' },
                    '100%': { opacity: '1', transform: 'scale(1)' },
                },
                pulseGlow: {
                    '0%, 100%': { boxShadow: '0 0 15px rgba(14, 165, 233, 0.5)' },
                    '50%': { boxShadow: '0 0 25px rgba(14, 165, 233, 0.8)' },
                }
            }
        },
    },
    plugins: [],
}
