# OwnChat - Personal AI Chat Application

A full-stack chat application built with Next.js, Flask, and PostgreSQL that allows users to chat with multiple AI models including GPT-4 and Claude.

## Features

### Authentication
- Email/password registration and login
- Google OAuth integration
- Session-based authentication with Flask-Login
- User profile management

### Chat System
- Create multiple chat sessions
- Select from various AI models (GPT-4, GPT-3.5 Turbo, Claude 3 variants)
- 20 message limit per chat
- Real-time message exchange
- Persistent chat history

### User Interface
- Clean, modern chat interface
- Left sidebar with chat list and user profile
- Main chat window with message history
- Auto-scroll to latest messages
- Message loading indicators
- Model selection for new chats

### Search & Organization
- Search through chat titles and message content
- Delete unwanted chats
- Chat sorting by last updated time

## Tech Stack

### Frontend
- **React 19** with TypeScript
- **Vite** for build tooling
- **React Router DOM** for navigation
- **Tailwind CSS** for styling
- **React Context** for state management
- **Axios** for API calls
- **Heroicons** for icons

### Backend
- **Flask** with Python
- **Flask-SQLAlchemy** for database ORM
- **Flask-Login** for authentication
- **Flask-CORS** for cross-origin requests
- **PostgreSQL** database

### AI Integration
- **OpenAI API** (GPT models)
- **Anthropic API** (Claude models)

## Installation & Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- PostgreSQL 12+

### 1. Clone the repository
```bash
git clone <repository-url>
cd ownchat
```

### 2. Database Setup
```bash
# Create PostgreSQL database
createdb ownchat

# Run the initialization script
psql -d ownchat -f database/init.sql
```

### 3. Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env with your configuration
# Required: DATABASE_URL, SECRET_KEY
# Optional: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, OPENAI_API_KEY, ANTHROPIC_API_KEY
```

### 4. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local

# Edit .env.local with your configuration
# Required: VITE_API_URL (usually http://localhost:5000/api)
# Optional: VITE_GOOGLE_CLIENT_ID
```

## Running the Application

### Option 1: Using Docker Compose (Recommended)
```bash
# Create .env file in the root directory with your API keys
cp .env.example .env

# Start all services
docker-compose up -d

# The application will be available at:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:5000
# - PostgreSQL: localhost:5432
```

### Option 2: Manual Setup

### 1. Start the Backend
```bash
cd backend
source venv/bin/activate
python app.py
```
The Flask API will be available at `http://localhost:5000`

### 2. Start the Frontend
```bash
cd frontend
npm run dev
```
The React app will be available at `http://localhost:3000`

## Environment Variables

### Backend (.env)
```bash
# Required
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://username:password@localhost/ownchat

# Optional - for Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Optional - for AI models
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Optional - CORS configuration
CORS_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```bash
VITE_API_URL=http://localhost:5000/api
VITE_GOOGLE_CLIENT_ID=your-google-client-id
```

## Setting up Google OAuth (Optional)

To enable Google login functionality:

1. **Create a Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Google+ API:**
   - In the API Library, search for "Google+ API"
   - Enable the API for your project

3. **Create OAuth 2.0 Credentials:**
   - Go to Credentials → Create Credentials → OAuth 2.0 Client IDs
   - Application type: Web application
   - Name: OwnChat
   - Authorized JavaScript origins: `http://localhost:3000`
   - Authorized redirect URIs: `http://localhost:3000`

4. **Configure Environment Variables:**
   - Copy the Client ID to both backend and frontend `.env` files
   - Copy the Client Secret to the backend `.env` file

5. **Test Google Login:**
   - The "Continue with Google" button will appear on login/register pages
   - Click it to redirect to Google's authentication flow

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/google-login` - Google OAuth login
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile

### Chats
- `GET /api/chats` - Get user's chats
- `POST /api/chats` - Create new chat
- `GET /api/chats/{id}` - Get chat with messages
- `DELETE /api/chats/{id}` - Delete chat
- `POST /api/chats/{id}/messages` - Send message
- `GET /api/chats/search` - Search chats

## Database Schema

### Users Table
- `id` (Primary Key)
- `email` (Unique)
- `password_hash`
- `name`
- `google_id` (Unique, optional)
- `avatar_url` (optional)
- `created_at`, `updated_at`

### Chats Table
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `title`
- `model`
- `created_at`, `updated_at`

### Messages Table
- `id` (Primary Key)
- `chat_id` (Foreign Key)
- `role` (user/assistant)
- `content`
- `created_at`

## Features in Detail

### Message Limit
Each chat is limited to 20 messages to ensure optimal performance and cost management for AI API calls.

### Auto-scroll
The chat window automatically scrolls to the latest message when new messages are added.

### Model Selection
Users can choose from different AI models when creating a new chat:
- **GPT-4**: Most capable, best for complex tasks
- **GPT-3.5 Turbo**: Fast and efficient for most conversations
- **Claude 3 Opus**: Anthropic's most powerful model
- **Claude 3 Sonnet**: Balanced performance and speed
- **Claude 3 Haiku**: Fast and lightweight

### Search Functionality
Users can search through their chat history by:
- Chat titles
- Message content
- Results are sorted by relevance and recency

## Security Features

- Password hashing using Werkzeug
- Session-based authentication with Flask-Login
- CORS protection
- SQL injection prevention through SQLAlchemy ORM
- Input validation and sanitization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please create an issue in the GitHub repository.