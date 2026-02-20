# Chatbot Application

A multi-agent intelligent chatbot system that routes user queries to specialized agents for accounting and customer support. Built with FastAPI backend, React frontend, and MongoDB for data persistence.

## 📋 Project Overview

This project is an AI-powered chatbot that uses LangGraph and LangChain to intelligently route user queries to specialized agents:

- **Accounting Agent**: Handles financial queries, employee data, assets, transactions, profit & loss statements, and chart of accounts
- **Support Agent**: Manages smart metering support, customer service, technical issues, billing, and outages

The system features:
- Real-time streaming chat responses
- Session-based chat history management
- MongoDB integration for persistent storage
- Modern React frontend with real-time UI updates
- Docker containerization for easy deployment

---

## 📊 Data (CSV Files)

The application uses CSV data stored in MongoDB for querying. The data is organized into two main categories:

### Accounting Data (`backend/data/accounting/`)

1. **Asset.csv** - Company assets and equipment information
2. **COA_final.csv** - Chart of Accounts (financial account structure)
3. **debt_final.csv** - Debt and liability information
4. **Human_Capital_final.csv** - Employee data including:
   - Employee names
   - Departments
   - Base salary
   - TDS Deducted
   - Net Pay
   - Last Paid Date
5. **profit&Loss_final.csv** - Profit and loss statements
6. **transaction.csv** - Transaction records

### Support Data (`backend/data/support/`)

1. **Smart_Metering_Support_Dataset.csv** - Smart metering support knowledge base containing:
   - Billing and accuracy information
   - Reliability and outage details
   - Technical documentation
   - Smart meter functionality guides

### Data Migration

CSV files are migrated to MongoDB on first run using `migrate_to_mongodb.py`. The data is stored in the `csv_data` collection for efficient querying.

---

## 🔧 Backend

### Technology Stack

- **FastAPI** - Modern Python web framework
- **LangChain** - LLM application framework
- **LangGraph** - State machine for multi-agent orchestration
- **MongoDB** - Database for chat history and CSV data storage
- **Pandas** - Data manipulation for CSV files
- **Uvicorn/Gunicorn** - ASGI server

### Architecture

The backend follows a multi-agent architecture:

1. **Supervisor Agent** - Routes queries to appropriate specialized agent
2. **Accounting Agent** - Handles financial and employee-related queries
3. **Support Agent** - Manages customer support and technical queries

### Process Flow

1. User sends a message via `/chat-stream` endpoint
2. System loads chat history from MongoDB (if exists)
3. Supervisor agent analyzes the query and routes to appropriate agent:
   - Accounting queries → `accounting` agent
   - Support queries → `support` agent
4. Specialized agent uses tools to search relevant CSV data
5. Agent generates response based on search results
6. Response is streamed back to the client
7. Complete conversation is saved to MongoDB with session_id

### Key Components

- `app/main.py` - FastAPI application and API endpoints
- `app/chatbot/graph.py` - LangGraph state machine definition
- `app/chatbot/agents/` - Agent implementations (supervisor, accounting, support)
- `app/services/mongodb_service.py` - Chat history management
- `app/services/mongodb_data_service.py` - CSV data storage/retrieval
- `app/services/data_manager.py` - Data search and query logic
- `app/chatbot/tools.py` - LangChain tools for data searching

---

## 🎨 Frontend

### Technology Stack

- **React 18** - UI library
- **Vite** - Build tool and dev server
- **CSS3** - Styling with modern gradients and animations
- **Nginx** - Production web server (Docker)

### Features

- Real-time streaming chat interface
- Message bubbles with user/assistant distinction
- Auto-scrolling to latest messages
- Session-based chat persistence
- Responsive design with modern UI
- Logo display in header

### Process Flow

1. User types message and clicks "Send" or presses Enter
2. Frontend sends POST request to `/chat-stream` endpoint
3. Response is streamed character-by-character
4. UI updates in real-time as chunks arrive
5. Complete message is displayed when streaming completes
6. Chat history is maintained in component state
7. Each session has a unique session_id for persistence

### Key Files

- `src/App.jsx` - Main chatbot component with chat logic
- `src/App.css` - Styling for chat interface
- `src/main.jsx` - React entry point
- `index.html` - HTML template

---

## 🔌 API Endpoints

### Chat Endpoints

#### `POST /chat-stream`
Stream chat responses in real-time.

**Request:**
```json
{
  "user_text": "What is the base salary of Amit Kumar?",
  "chat": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}],
  "session_id": "session_1234567890"
}
```

**Response:** Streaming text/plain response

---

#### `POST /get-chat-response`
Get complete chat response (non-streaming).

**Request:** Same as `/chat-stream`

**Response:**
```
Complete response text
```

---

### Chat History Endpoints

#### `POST /save-chat`
Save chat history to MongoDB.

**Request:**
```json
{
  "session_id": "session_1234567890",
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Chat history saved for session_id: session_1234567890",
  "session_id": "session_1234567890",
  "message_count": 2
}
```

---

#### `GET /get-chat-history/{session_id}`
Retrieve chat history by session ID.

**Example:** `GET /get-chat-history/session_1234567890`

**Response:**
```json
{
  "status": "success",
  "session_id": "session_1234567890",
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ],
  "message_count": 2
}
```

---

#### `GET /list-all-sessions`
List all chat sessions with metadata.

**Response:**
```json
{
  "status": "success",
  "sessions": [
    {
      "session_id": "session_1234567890",
      "message_count": 5,
      "updated_at": "2024-01-15T10:30:00"
    }
  ],
  "total_sessions": 1
}
```

---

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

---

## 🚀 Steps to Run

### Prerequisites

- Docker and Docker Compose installed
- (For local development) Python 3.11+, Node.js 18+

### Option 1: Docker (Recommended)

1. **Clone/Navigate to the project directory:**
   ```bash
   cd /path/to/radius
   ```

2. **Create backend environment file:**
   ```bash
   cd backend
   cp .env.example .env  # Or create .env manually
   ```
   
   Add your OpenAI API key to `backend/.env`:
   ```
   OPENAI_API_KEY=your_api_key_here
   CHAT_MODEL=gpt-4o-mini
   MONGODB_URI=mongodb://mongodb:27017
   MONGODB_DB=chatbot_db
   ```

3. **Migrate CSV data to MongoDB (first time only):**
   ```bash
   docker-compose up mongodb -d
   # Wait a few seconds for MongoDB to start
   cd backend
   python migrate_to_mongodb.py
   ```

4. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```

5. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

6. **Stop services:**
   ```bash
   docker-compose down
   ```

---

### Option 2: Local Development

#### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file:**
   ```
   OPENAI_API_KEY=your_api_key_here
   CHAT_MODEL=gpt-4o-mini
   MONGODB_URI=mongodb://localhost:27017
   MONGODB_DB=chatbot_db
   ```

5. **Start MongoDB (if using):**
   ```bash
   docker-compose up mongodb -d
   ```

6. **Migrate CSV data (if using MongoDB):**
   ```bash
   python migrate_to_mongodb.py
   ```

7. **Run backend:**
   ```bash
   sh run.sh
   ```

#### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **Access frontend:**
   - Development: http://localhost:3000 (or port shown in terminal)

---

### Rebuilding After Changes

#### Docker

```bash
# Rebuild and restart all services
docker-compose up --build

# Rebuild specific service
docker-compose build frontend
docker-compose up frontend

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### Local Development

**Backend:**
```bash
cd backend
# Make changes, then restart
sh run.sh
```

**Frontend:**
```bash
cd frontend
# Make changes, Vite will auto-reload
npm run dev
```

---

## 📁 Project Structure

```
radius/
├── backend/
│   ├── app/
│   │   ├── chatbot/
│   │   │   ├── agents/        # Agent implementations
│   │   │   ├── graph.py       # LangGraph state machine
│   │   │   ├── prompts.py     # Agent prompts
│   │   │   ├── state.py       # State definitions
│   │   │   └── tools.py       # LangChain tools
│   │   ├── services/          # Business logic services
│   │   ├── utils/             # Utilities and config
│   │   └── main.py            # FastAPI app
│   ├── data/                  # CSV data files
│   │   ├── accounting/
│   │   └── support/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── run.sh
│   └── migrate_to_mongodb.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main component
│   │   ├── App.css
│   │   └── main.jsx
│   ├── image/                # Assets
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── README.md
```

---

## 🔍 Testing the API

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# List all sessions
curl http://localhost:8000/list-all-sessions

# Get chat history
curl http://localhost:8000/get-chat-history/session_1234567890

# Send chat message
curl -X POST http://localhost:8000/chat-stream \
  -H "Content-Type: application/json" \
  -d '{
    "user_text": "What is the base salary of Amit Kumar?",
    "session_id": "test_session"
  }'
```

### Using the Frontend

Simply open http://localhost:3000 in your browser and start chatting!

---

## 📝 Notes

- Chat history is automatically saved during conversations
- Each chat session has a unique `session_id` for tracking
- MongoDB is optional - the system falls back to in-memory storage if MongoDB is unavailable
- CSV data must be migrated to MongoDB before the first query
- The supervisor agent automatically routes queries to the appropriate specialist agent

---

## 🛠️ Troubleshooting

**MongoDB connection issues:**
- Ensure MongoDB container is running: `docker-compose ps`
- Check MongoDB logs: `docker-compose logs mongodb`

**Backend not starting:**
- Verify `.env` file exists with `OPENAI_API_KEY`
- Check backend logs: `docker-compose logs backend`

**Frontend not connecting to backend:**
- Verify backend is running on port 8000
- Check CORS settings in `backend/app/main.py`
- Ensure API_URL in frontend points to correct backend URL

**CSV data not found:**
- Run migration script: `python backend/migrate_to_mongodb.py`
- Verify CSV files exist in `backend/data/` directories

---

## 📄 License

This project is for internal use.

