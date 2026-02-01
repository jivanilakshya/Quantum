# Quantum Backend - FastAPI with Vexa AI Integration

## Setup Instructions

### 1. Install Dependencies

```bash
cd quantum-backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `quantum-backend` directory:

```bash
# Vexa AI API Configuration
VEXA_API_KEY=your_vexa_api_key_here
VEXA_BASE_URL=https://api.cloud.vexa.ai

# Database Configuration
DATABASE_URL=sqlite:///./quantum.db

# JWT Configuration
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Configuration
FRONTEND_URL=http://localhost:3000

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

**IMPORTANT**: Replace `your_vexa_api_key_here` with your actual Vexa API key from [vexa.ai/dashboard/api-keys](https://vexa.ai/dashboard/api-keys)

### 3. Run the Server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/signup` - Create new account

### Bot Management
- `POST /api/bots/start` - Start a bot for a meeting
- `POST /api/bots/stop` - Stop a bot (IMPORTANT: Frees API credits!)
- `GET /api/bots/status` - Get status of running bots
- `PUT /api/bots/{platform}/{meeting_id}/language` - Update bot language

### Meeting Management
- `GET /api/meetings/` - List all meetings
- `GET /api/meetings/{platform}/{meeting_id}/transcript` - Get real-time transcript
- `PATCH /api/meetings/{platform}/{meeting_id}` - Update meeting metadata
- `DELETE /api/meetings/{platform}/{meeting_id}` - Delete transcripts

## Frontend Configuration

In the `quantum-frontend` directory, create a `.env.local` file:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Demo Credentials

For testing authentication:
- Email: `demo@quantum.ai`
- Password: `demo123`

## Vexa AI Integration

The backend integrates with Vexa AI for:
1. **Bot Management**: Start/stop transcription bots
2. **Real-time Transcription**: Get live meeting transcripts
3. **Speaker Diarization**: Identify different speakers
4. **Multi-language Support**: English, Hindi, Gujarati, Spanish, French

### Important Notes

- **Always stop bots** after meetings to free up API credits
- Bot takes ~10 seconds to join after requesting
- For Teams meetings, passcode is required in the URL
- Transcripts are available in real-time during the meeting

## Project Structure

```
quantum-backend/
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── api/
│   ├── auth.py            # Authentication endpoints
│   ├── bots.py            # Bot management endpoints
│   └── meetings.py        # Meeting management endpoints
└── services/
    └── vexa_client.py     # Vexa AI API client
```

## Development

### Running in Development Mode

```bash
python main.py
```

The server will auto-reload on code changes.

### Testing API Endpoints

Use the Swagger UI at http://localhost:8000/docs to test endpoints interactively.

## Production Deployment

For production:
1. Change `SECRET_KEY` to a secure random string
2. Use a production database (PostgreSQL recommended)
3. Set `reload=False` in uvicorn
4. Use a production ASGI server (gunicorn + uvicorn workers)
5. Enable HTTPS
6. Set proper CORS origins

## Troubleshooting

### "Failed to start bot"
- Check that your Vexa API key is correct
- Verify the meeting URL format is correct
- Ensure you have API credits available

### "CORS Error"
- Check that `FRONTEND_URL` in `.env` matches your frontend URL
- Verify CORS middleware is properly configured

### "Database Error"
- Ensure the database file has write permissions
- For production, use PostgreSQL instead of SQLite

## Support

For Vexa AI API issues, contact support via [vexa.ai](https://vexa.ai)
