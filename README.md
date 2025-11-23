# Memory Card Game - Deployment & Usage Guide

## 📋 Overview
Complete memory card game system with:
- **Backend**: FastAPI + SQLite/PostgreSQL
- **Frontend**: React + Vite
- **Admin Panel**: Statistics & Settings Management
- **Embeddable**: Ready for iframe integration

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- Node.js 16+
- npm or yarn

### Backend Setup

1. **Navigate to backend directory**:
```bash
cd backend
```

2. **Create virtual environment** (recommended):
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Run the server**:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Frontend Setup

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Run development server**:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

---

## 🎮 Usage

### Playing the Game
1. Open `http://localhost:3000`
2. Optionally enter your name
3. Click "Start Game"
4. Click cards to flip and find matching pairs
5. Complete all matches to finish

### Admin Panel
1. Navigate to `http://localhost:3000/admin`
2. View statistics (total games, players, scores)
3. Configure game rules:
   - Number of card pairs (2-16)
   - Time limit (optional)
   - Match points
   - Mismatch penalty
   - Time bonus toggle

---

## 🔧 Configuration

### Backend Configuration

**Database**: Edit `app/database.py` to switch from SQLite to PostgreSQL:
```python
# Change this line:
SQLALCHEMY_DATABASE_URL = "sqlite:///./memory_game.db"

# To PostgreSQL:
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"
```

**CORS**: Update allowed origins in `app/main.py` for production:
```python
allow_origins=["https://yourdomain.com"]  # Instead of "*"
```

### Frontend Configuration

**API URL**: Edit `frontend/.env`:
```
VITE_API_URL=http://your-backend-url:8000
```

---

## 📦 Production Deployment

### Backend Deployment

**Option 1: Docker** (Recommended)
```dockerfile
# Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t memory-game-backend .
docker run -p 8000:8000 memory-game-backend
```

**Option 2: Direct Deployment**
```bash
# Install dependencies
pip install -r requirements.txt

# Run with gunicorn (production server)
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend Deployment

1. **Build for production**:
```bash
cd frontend
npm run build
```

2. **Deploy the `dist` folder** to:
   - Static hosting (Netlify, Vercel, GitHub Pages)
   - CDN
   - Web server (Nginx, Apache)

**Example Nginx configuration**:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /path/to/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 🔗 Iframe Embedding

### Basic Embed
```html
<iframe 
  src="https://yourdomain.com" 
  width="100%" 
  height="800px" 
  frameborder="0"
  title="Memory Card Game"
  style="border-radius: 12px;"
></iframe>
```

### Responsive Embed
```html
<div style="position: relative; padding-bottom: 75%; height: 0;">
  <iframe 
    src="https://yourdomain.com" 
    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
    frameborder="0"
  ></iframe>
</div>
```

### Demo
Open `embed-demo.html` in a browser to see embedding in action.

---

## 🗄️ Database Schema

### Tables

**game_settings**
- Game configuration (match points, penalties, time limits)

**games**
- Individual game sessions
- Cards state, score, moves, completion time

**player_stats**
- Player records (best score, best time, total games)

---

## 🔌 API Endpoints

### Game Endpoints
- `POST /game/start` - Create new game
- `GET /game/{id}` - Get game state
- `POST /game/{id}/flip` - Flip a card
- `POST /game/{id}/reset-flipped` - Reset flipped cards

### Admin Endpoints
- `GET /admin/settings` - Get game settings
- `PUT /admin/settings` - Update settings
- `GET /admin/stats` - Get aggregate statistics
- `GET /admin/leaderboard` - Get top players

Full API documentation: `http://localhost:8000/docs`

---

## 🛠️ Troubleshooting

### Backend Issues

**Database locked** (SQLite):
- Only one process can write at a time
- Switch to PostgreSQL for production

**CORS errors**:
- Check `allow_origins` in `app/main.py`
- Ensure frontend URL is allowed

### Frontend Issues

**API connection failed**:
- Verify backend is running
- Check `.env` file has correct API URL
- Check browser console for errors

**Build errors**:
- Delete `node_modules` and reinstall: `npm install`
- Clear cache: `npm cache clean --force`

---

## 📈 Scaling for Production

### For High Traffic

1. **Backend**:
   - Use PostgreSQL instead of SQLite
   - Deploy multiple instances behind load balancer
   - Add Redis for caching
   - Use connection pooling

2. **Frontend**:
   - Deploy to CDN (Cloudflare, AWS CloudFront)
   - Enable gzip compression
   - Optimize images and assets

3. **Database**:
   - Use managed PostgreSQL (AWS RDS, DigitalOcean)
   - Regular backups
   - Monitor query performance

---

## 🔐 Security Considerations

### Production Checklist
- [ ] Change `allow_origins` from `*` to specific domains
- [ ] Add authentication for admin endpoints
- [ ] Use HTTPS for all connections
- [ ] Set up rate limiting
- [ ] Enable database backups
- [ ] Use environment variables for secrets
- [ ] Add input validation and sanitization

---

## 📝 License & Credits

Built with:
- FastAPI (Backend)
- React + Vite (Frontend)
- SQLAlchemy (Database)
- Vanilla CSS (Styling)

---

## 🆘 Support

For issues and questions:
1. Check API documentation: `http://localhost:8000/docs`
2. Review browser console for errors
3. Check backend logs for errors
4. Verify all dependencies are installed

---

**Happy Gaming! 🎮**
