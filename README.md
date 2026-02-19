# OrchestrAI Interview Lab

A comprehensive, multi-agent AI-driven technical interview platform that automates candidate evaluation across Data Structures & Algorithms (DSA), System Design, and Behavioral competencies. The system leverages multi-agent orchestration to conduct realistic, comprehensive technical interviews with AI-driven assessments.

## Project Overview

OrchestrAI Interview Lab is a production-grade interview automation system built on a distributed agent architecture. It orchestrates multiple specialized AI agents to conduct technical interviews, evaluate coding solutions, assess system design capabilities, and provide hiring recommendations. The system integrates vector-based memory, semantic retrieval, and multi-turn conversation handling for comprehensive candidate evaluation.

### Key Features

- **Multi-Phase Interview Workflow**: Sequential interview phases covering resume analysis, DSA questions, code evaluation, system design, and behavioral assessment
- **Distributed Agent Architecture**: Specialized agents for recruitment, DSA interviewing, code evaluation, system design, behavioral assessment, and hallucination detection
- **Real-Time Evaluation**: Live agent messaging and scoring feedback through WebSocket connections
- **Advanced Memory System**: Vector-based embedding storage with semantic search capabilities using Qdrant
- **LLM Flexibility**: Support for both Groq cloud API and local Ollama models with configurable selection
- **Cross-Agent Debate**: Critic and final decision agents synthesize evaluations from multiple specialized agents
- **Persistent Interview History**: SQLite/PostgreSQL storage of session data and interview results
- **Resume Intelligence**: Automated resume parsing and skill extraction for interview customization
- **Interactive Code Evaluation**: Real-time submission and evaluation of code solutions with syntax analysis

## Architecture

### System Design

```
Frontend (React + TypeScript)
         |
         | WebSocket / REST API
         |
FastAPI Backend
    ├── API Routes (FastAPI)
    ├── WebSocket Handler
    └── Agent Orchestration
        ├── Message Bus (Pub/Sub)
        ├── State Machine
        └── Agent Coordinator
            ├── Recruiter Agent
            ├── DSA Interviewer Agent
            ├── Code Evaluator Agent
            ├── System Design Agent
            ├── Behavioral Agent
            ├── Hallucination Detector
            ├── Critic Agent
            └── Final Decision Agent

Memory & Storage
    ├── Vector Store (Qdrant)
    │   └── Embeddings (sentence-transformers)
    ├── Database (SQLite/PostgreSQL)
    │   └── Interview History & Sessions
    └── RAG Components
        ├── DSA Knowledge Base
        └── System Design Knowledge Base
```

### Backend Structure

```
backend/
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Environment and settings management
│   ├── agents/                 # Agent implementations
│   │   ├── base.py             # BaseAgent abstract class
│   │   ├── recruiter.py        # Resume analysis and skill extraction
│   │   ├── dsa_interviewer.py   # DSA question generation
│   │   ├── code_evaluator.py    # Code solution evaluation
│   │   ├── system_design.py     # System design question assessment
│   │   ├── behavioral.py        # Behavioral question handling
│   │   ├── hallucination_detector.py  # Fact verification
│   │   ├── critic.py            # Cross-agent analysis
│   │   └── final_decision.py    # Hiring recommendation synthesis
│   ├── orchestrator/           # Orchestration components
│   │   ├── message_bus.py      # Pub/Sub message routing
│   │   ├── state_machine.py    # Interview state management
│   │   └── engine.py           # Orchestration engine
│   ├── memory/                 # Memory and storage interfaces
│   │   ├── interface.py        # Memory abstraction
│   │   ├── vector_store.py     # Qdrant vector storage
│   │   └── postgres_store.py   # PostgreSQL persistence
│   ├── api/                    # API handlers
│   │   ├── routes.py           # REST endpoints
│   │   └── websocket.py        # WebSocket handlers
│   ├── models/                 # Data models and enums
│   │   ├── schemas.py          # Pydantic schemas
│   │   └── enums.py            # Interview state and agent enums
│   ├── rag/                    # Retrieval-Augmented Generation
│   │   ├── embedder.py         # Embedding generation
│   │   ├── retriever.py        # Document retrieval
│   │   ├── dsa_rag.py          # DSA knowledge base
│   │   └── sysdesign_rag.py    # System design knowledge base
│   └── tools/                  # Utility tools
│       ├── code_runner.py      # Code execution sandbox
│       └── rubric_loader.py    # Evaluation rubric management
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
└── test_backend.py             # Testing utilities
```

### Frontend Structure

```
frontend/
├── src/
│   ├── main.tsx               # Application entry point
│   ├── App.tsx                # Main application component
│   ├── App.css                # Application styles
│   ├── index.css              # Global styles
│   ├── assets/                # Static resources
│   └── types/
│       └── interview.ts       # TypeScript type definitions
├── public/                    # Public static assets
├── package.json              # npm dependencies
├── vite.config.ts            # Vite build configuration
├── tsconfig.json             # TypeScript configuration
└── eslint.config.js          # Linting configuration
```

## Technical Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | FastAPI | 0.109.0 | REST API and ASGI server |
| ASGI Server | Uvicorn | 0.27.0 | Async HTTP server with WebSocket support |
| Validation | Pydantic | 2.5.3 | Data validation and serialization |
| Language Models | Groq / Ollama | - | LLM inference (cloud/local) |
| Vector Database | Qdrant | 1.7.0 | Vector embeddings storage |
| Embeddings | sentence-transformers | 2.3.1 | Text embedding generation |
| Database | PostgreSQL/SQLite | 2.9.9 / SQLAlchemy 2.0.25 | Persistent storage |
| Authentication | python-jose | 3.3.0 | JWT token handling |
| Real-Time | WebSockets | 12.0 | Live agent messaging |
| HTTP Client | httpx | 0.26.0 | Async HTTP requests |
| Utilities | NumPy, Pandas | 1.26.3, 2.1.4 | Numerical and data operations |
| Testing | pytest, pytest-asyncio | 7.4.4, 0.23.3 | Unit and async testing |
| Code Quality | black, ruff | 24.1.1, 0.1.14 | Code formatting and linting |
| PDF Processing | PyPDF2 | 3.0.1 | Resume PDF extraction |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | React | 19.2.0 | UI library |
| Language | TypeScript | 5.9.3 | Type-safe JavaScript |
| Build Tool | Vite | 7.3.1 | Fast module bundler |
| State Management | Zustand | 5.0.11 | Lightweight state library |
| HTTP Client | axios | 1.13.5 | Promise-based HTTP requests |
| Flow Diagram | @xyflow/react | 12.10.0 | Node and edge visualization |
| Charts | recharts | 3.7.0 | Data visualization |
| Icons | lucide-react | 0.563.0 | Icon library |
| Styling | Tailwind CSS | 4.1.18 | Utility-first CSS framework |
| Linting | ESLint | 9.39.1 | Code quality checking |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Containerization | Docker | Application containerization |
| Orchestration | Docker Compose | Multi-container management |
| Vector Store | Qdrant | Vector similarity search |

## Setup and Installation

### Prerequisites

- Python 3.10 or higher
- Node.js 18+ and npm
- Docker and Docker Compose
- Groq API key (optional, for cloud-based LLM) or local Ollama installation

### Environment Configuration

1. Navigate to the backend directory and create a `.env` file:

```bash
cd backend
cp env_groq_template .env
```

2. Configure your `.env` file with required variables:

```env
# LLM Configuration
USE_GROQ=true
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama3-8b-8192
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3:mini

# Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=interview_memory

# Database
DATABASE_URL=sqlite:///./interview_data.db

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIM=384

# Inference Parameters
MAX_RETRIEVAL_RESULTS=5
CONFIDENCE_THRESHOLD=0.7

# Environment
ENVIRONMENT=development
```

### Quick Start

#### Option 1: Using PowerShell Script (Windows)

```powershell
.\start.ps1
```

This script:
- Starts Docker Compose services (Qdrant vector database)
- Activates Python virtual environment
- Launches FastAPI backend on port 8000
- Starts frontend dev server on port 5173

#### Option 2: Manual Setup

**Backend Setup:**

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
# or
source venv/bin/activate     # Unix/macOS

# Install dependencies
pip install -r requirements.txt

# Start backend server
python -m uvicorn src.main:app --reload
```

**Frontend Setup (in new terminal):**

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Infrastructure:**

```bash
# Start Qdrant vector database
docker-compose up -d
```

**Access the Application:**

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Qdrant Dashboard: http://localhost:6333/dashboard

## Agent Architecture

### Agent Types and Responsibilities

#### 1. Recruiter Agent
- Analyzes candidate resumes using PDF extraction
- Extracts skills, experience, and background information
- Generates customized difficulty levels based on candidate profile
- Initiates interview workflow

#### 2. DSA Interviewer Agent
- Generates Data Structures and Algorithms questions
- Adjusts difficulty dynamically based on performance
- Retrieves relevant DSA problems from knowledge base
- Provides domain-specific hints and guidance

#### 3. Code Evaluator Agent
- Analyzes submitted code solutions
- Checks algorithmic correctness and efficiency
- Evaluates code quality, readability, and best practices
- Generates constructive feedback

#### 4. System Design Agent
- Creates system design scenario questions
- Evaluates architectural decisions
- Analyzes scalability and trade-offs
- Retrieves relevant system design patterns

#### 5. Behavioral Agent
- Conducts behavioral and situational questions
- Assesses soft skills and cultural fit
- Evaluates leadership and problem-solving approach
- Provides behavioral competency scoring

#### 6. Hallucination Detector Agent
- Validates factual claims made during interviews
- Prevents false information propagation
- Cross-references agent responses
- Ensures response accuracy

#### 7. Critic Agent
- Performs meta-analysis of all agent evaluations
- Identifies inconsistencies in assessment
- Synthesizes diverse perspectives
- Prepares data for final decision

#### 8. Final Decision Agent
- Aggregates all evaluation scores
- Generates comprehensive hiring recommendation
- Produces detailed interview report
- Calculates final hire/no-hire decision with confidence

### Message Bus and Communication

The message bus implements a publish-subscribe pattern enabling asynchronous communication between agents:

- **Targeted Messaging**: Agents can send messages to specific recipients
- **Broadcast Messages**: Decisions shared with all agents
- **Message History**: Complete audit trail of all communications
- **Filtering Capabilities**: Query message history by sender, receiver, type

### State Machine

Manages the interview workflow progression through defined states:

1. `INIT` - Initialization and setup
2. `RESUME_ANALYSIS` - Resume processing and evaluation
3. `DSA_PHASE` - Data structures and algorithms questions
4. `SYSTEM_DESIGN_PHASE` - System design assessment
5. `BEHAVIORAL_PHASE` - Behavioral and soft skills evaluation
6. `CROSS_AGENT_DEBATE` - Multi-agent discussion and synthesis
7. `FINAL_DECISION` - Final hiring recommendation
8. `COMPLETED` - Interview concluded

## API Endpoints

### Initialize Interview
```
POST /api/initialize
Content-Type: application/json

{
  "candidate_name": "string",
  "resume_text": "string",
  "difficulty": "EASY|MEDIUM|HARD"
}

Response:
{
  "session_id": "uuid",
  "status": "initialized",
  "next_phase": "dsa|system_design|behavioral"
}
```

### Submit Resume PDF
```
POST /api/upload-resume
Content-Type: multipart/form-data

file: <pdf_file>
session_id: <uuid>

Response:
{
  "extracted_text": "string",
  "skills": ["skill1", "skill2"],
  "experience_years": number
}
```

### Get Question
```
GET /api/get-question?session_id=<uuid>&phase=<phase>

Response:
{
  "question": "string",
  "context": "string",
  "examples": ["array"],
  "constraints": ["array"]
}
```

### Submit Answer/Code
```
POST /api/submit-answer
Content-Type: application/json

{
  "session_id": "uuid",
  "phase": "dsa|system_design|behavioral",
  "answer": "string"
}

Response:
{
  "received": true,
  "evaluation_in_progress": true
}
```

### Get Evaluation
```
GET /api/get-evaluation?session_id=<uuid>

Response:
{
  "evaluations": [
    {
      "agent": "code_evaluator",
      "score": number,
      "feedback": "string",
      "timestamp": "datetime"
    }
  ],
  "overall_score": number
}
```

### Get Interview Report
```
GET /api/interview-report?session_id=<uuid>

Response:
{
  "session_id": "uuid",
  "candidate": "string",
  "completion_status": "completed|in_progress",
  "scores": {
    "dsa": number,
    "system_design": number,
    "behavioral": number,
    "overall": number
  },
  "recommendation": "HIRE|NO_HIRE|MAYBE",
  "detailed_feedback": "string",
  "time_taken": "string"
}
```

### WebSocket Connection
```
WebSocket /ws/{session_id}

Receive real-time messages:
{
  "type": "agent_message|evaluation|status|progress",
  "sender": "agent_name",
  "content": "message_content",
  "timestamp": "datetime"
}
```

## Configuration

### Model Selection

The system supports configurable LLM backends:

**Groq (Cloud-Based, Faster Inference):**
```env
USE_GROQ=true
GROQ_API_KEY=gsk_your_api_key_here
GROQ_MODEL=llama3-8b-8192
```

**Ollama (Local, Privacy-Preserving):**
```env
USE_GROQ=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3:mini
```

### Embedding Configuration

Default configuration uses `all-MiniLM-L6-v2`:
- Embedding dimension: 384
- Suitable for general-purpose semantic search
- Optional alternatives:
  - `all-mpnet-base-v2`: 768-dimensional, higher quality
  - `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`: 768-dimensional, multilingual

### Database Selection

**SQLite (Development):**
```env
DATABASE_URL=sqlite:///./interview_data.db
```

**PostgreSQL (Production):**
```env
DATABASE_URL=postgresql://user:password@localhost/orchestrai_db
```

## Interview Workflow

### Phase 1: Resume Analysis
1. Candidate uploads resume (PDF or text)
2. Recruiter Agent extracts skills and experience
3. Difficulty level auto-calibrated based on background
4. Initial skill profile generated

### Phase 2: DSA Assessment
1. DSA Interviewer generates context-appropriate question
2. Candidate submits code solution
3. Code Evaluator assesses correctness and efficiency
4. Real-time feedback provided via WebSocket

### Phase 3: System Design
1. System Design Agent creates architecture scenario
2. Candidate provides design approach
3. Evaluator assesses scalability and design patterns
4. Trade-offs discussed and documented

### Phase 4: Behavioral Questions
1. Behavioral Agent poses situational questions
2. Candidate responses evaluated for soft skills
3. Communication and leadership assessed
4. Team fit evaluated

### Phase 5: Cross-Agent Synthesis
1. Critic Agent analyzes all evaluations
2. Inconsistencies identified and resolved
3. Pattern recognition across performance
4. Final deliberation conducted

### Phase 6: Final Decision
1. Final Decision Agent synthesizes all data
2. Confidence score calculated
3. Hiring recommendation generated (HIRE/NO_HIRE/MAYBE)
4. Comprehensive report produced

## Development

### Running Tests

```bash
cd backend
pip install pytest pytest-asyncio
pytest test_backend.py -v
```

### Code Quality

**Format Code:**
```bash
cd backend
black src/
```

**Lint Code:**
```bash
cd backend
ruff check src/ --fix
```

**Frontend Linting:**
```bash
cd frontend
npm run lint
```

### Building Frontend

**Development Build:**
```bash
cd frontend
npm run dev
```

**Production Build:**
```bash
cd frontend
npm run build
```

## Database Schema

### Interviews Table
```sql
CREATE TABLE interviews (
  id UUID PRIMARY KEY,
  candidate_name VARCHAR(255),
  resume_text TEXT,
  difficulty_level VARCHAR(20),
  created_at TIMESTAMP,
  completed_at TIMESTAMP,
  overall_score FLOAT,
  recommendation VARCHAR(50),
  status VARCHAR(50)
);
```

### Agent Messages Table
```sql
CREATE TABLE agent_messages (
  id UUID PRIMARY KEY,
  session_id UUID FOREIGN KEY,
  sender VARCHAR(100),
  receiver VARCHAR(100),
  message_type VARCHAR(50),
  content TEXT,
  confidence FLOAT,
  timestamp TIMESTAMP
);
```

### Evaluations Table
```sql
CREATE TABLE evaluations (
  id UUID PRIMARY KEY,
  session_id UUID FOREIGN KEY,
  agent_name VARCHAR(100),
  phase VARCHAR(50),
  score FLOAT,
  feedback TEXT,
  metadata JSON,
  created_at TIMESTAMP
);
```

## Performance Optimization

### Vector Store Optimization
- Batch embeddings for large datasets
- Use appropriate vector dimensions (smaller = faster)
- Implement hybrid search combining semantic and keyword matching
- Configure Qdrant pagination for large result sets

### LLM Inference
- Use streaming responses for long-form generation
- Implement request batching for concurrent queries
- Cache embeddings for repeated queries
- Optimize prompt engineering for faster token consumption

### Database Optimization
- Implement connection pooling
- Create indexes on frequently queried fields
- Use pagination for large result sets
- Archive completed interviews periodically

## Troubleshooting

### Qdrant Connection Issues
```bash
# Verify Qdrant is running
curl -s http://localhost:6333/health

# Check Docker logs
docker logs orchestrai_qdrant
```

### LLM API Errors
- Verify Groq API key is valid: `echo $env:GROQ_API_KEY`
- Check rate limits and quota usage in Groq console
- For Ollama, ensure service is running: `curl http://localhost:11434/api/tags`

### WebSocket Connection Failures
- Verify backend is running on port 8000
- Check CORS configuration in FastAPI settings
- Inspect browser console for connection errors

### Database Errors
- For SQLite: ensure database file permissions are correct
- For PostgreSQL: verify connection string and server availability
- Check database logs for constraint violations

## Production Deployment

### Docker Deployment

```bash
# Build backend image
docker build -t orchestrai-backend ./backend

# Use docker-compose for full stack
docker-compose up -d
```

### Environment Variables for Production

```env
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@db-server/orchestrai
QDRANT_HOST=qdrant-server
QDRANT_PORT=6333
USE_GROQ=true
GROQ_API_KEY=your_production_key
```

### Scaling Considerations

- Use load balancer for multiple backend instances
- Implement session persistence for state management
- Use managed Qdrant service (Qdrant Cloud)
- Configure PostgreSQL replication for high availability
- Implement caching layer (Redis) for frequently accessed data

## Contributing

### Code Style
- Python: Follow PEP 8 (enforced by black and ruff)
- TypeScript: Follow ESLint configuration
- Commit messages: Use conventional commits format

### Adding New Agents

1. Extend `BaseAgent` class
2. Implement `act()` method with LLM interaction
3. Register in `main.py` agents initialization
4. Update state machine transitions if needed
5. Add corresponding routes in API

### Adding New Endpoints

1. Create route in `src/api/routes.py`
2. Define Pydantic schema for request/response
3. Add WebSocket handler if needed in `src/api/websocket.py`
4. Document in API Endpoints section