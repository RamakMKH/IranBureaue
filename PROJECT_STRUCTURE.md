# 🏗️ Project Structure - News Management System v2.0

Detailed documentation of the project architecture and file organization.

---

## 📁 Directory Tree

```
IranBureau/
├── app/                          # Main application package
│   ├── __init__.py              # App package initialization
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Configuration management
│   ├── database.py              # Database setup
│   ├── dependencies.py          # FastAPI dependencies
│   │
│   ├── models/                  # Database models (SQLAlchemy)
│   │   ├── __init__.py
│   │   └── news.py             # News model with status enum
│   │
│   ├── schemas/                 # Pydantic schemas
│   │   ├── __init__.py
│   │   └── news.py             # Request/Response validation
│   │
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication & sessions
│   │   ├── crawler.py          # News crawling from Webz.io
│   │   ├── translator.py       # Translation (Gemini + Google)
│   │   └── telegram.py         # Telegram publishing
│   │
│   ├── repositories/            # Data access layer
│   │   ├── __init__.py
│   │   └── news_repository.py  # News CRUD operations
│   │
│   ├── routers/                 # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py             # Login/Logout routes
│   │   ├── news.py             # News CRUD routes
│   │   └── admin.py            # Admin operations routes
│   │
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       ├── proxy.py            # SOCKS5 proxy management
│       ├── scoring.py          # News scoring algorithm
│       └── logging.py          # Advanced logging utilities
│
├── static/                      # Frontend files
│   ├── index.html              # Login page
│   ├── dashboard.html          # Main dashboard
│   ├── advanced_crawl.html     # Advanced crawler UI
│   └── logs.html               # Logs viewer
│
├── tests/                       # Test suite (optional)
│   ├── __init__.py
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
│
├── .env                         # Environment variables (not in git)
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker Compose config
├── Makefile                    # Development commands
├── setup.py                    # Setup and testing utility
├── database.py                 # Database module (root level)
├── README.md                   # Main documentation
├── MIGRATION.md                # v1→v2 migration guide
├── FILE_CHECKLIST.md           # Complete file checklist
├── PROJECT_STRUCTURE.md        # This file
└── LICENSE                     # MIT License

```

---

## 🎯 Architecture Pattern

The project follows **Clean Architecture** principles with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│                 Presentation Layer               │
│  (FastAPI Routes, HTML Templates, API Docs)     │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│              Application Layer                   │
│      (Business Logic, Services, DTOs)           │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│               Domain Layer                       │
│    (Models, Entities, Business Rules)           │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│           Infrastructure Layer                   │
│  (Database, External APIs, File System)         │
└─────────────────────────────────────────────────┘
```

---

## 📦 Package Details

### 1. **app/models/** - Domain Models

Contains SQLAlchemy ORM models representing database tables.

**Files:**
- `news.py`: News model with relationships and indexes

**Key Features:**
- Enum-based status management
- Automatic timestamps
- Optimized indexes for queries
- Helper methods for common operations

**Example:**
```python
from app.models.news import News, NewsStatus

# Create news
news = News(
    title="Breaking News",
    status=NewsStatus.COLLECTED
)
```

---

### 2. **app/schemas/** - Data Transfer Objects

Pydantic models for request/response validation.

**Files:**
- `news.py`: All request/response schemas

**Key Features:**
- Automatic validation
- Type checking
- Documentation generation
- Serialization/deserialization

**Schema Types:**
- Request schemas (input validation)
- Response schemas (output formatting)
- Config schemas (settings validation)

**Example:**
```python
from app.schemas.news import NewsResponse

response = NewsResponse(
    id=1,
    title="News Title",
    status="collected"
)
```

---

### 3. **app/services/** - Business Logic

Core business logic and external service integrations.

#### `auth.py` - Authentication Service
- Session management with expiration
- Password verification (bcrypt)
- Secure session tokens
- Session cleanup

#### `crawler.py` - Crawler Service
- Webz.io API integration
- News collection with scoring
- Duplicate detection
- Rate limiting and retries
- Multi-language support

#### `translator.py` - Translation Service
- Gemini AI translation (primary)
- Google Translate fallback
- Text preprocessing
- Error handling

#### `telegram.py` - Telegram Service
- Bot integration
- Channel publishing
- Message formatting
- Connection testing

**Example:**
```python
from app.services.crawler import crawler_service

news_list = crawler_service.crawl_news(
    db=db,
    language="english",
    limit=50
)
```

---

### 4. **app/repositories/** - Data Access Layer

Repository pattern for database operations.

**Files:**
- `news_repository.py`: All news-related queries

**Key Features:**
- CRUD operations
- Complex queries with filters
- Transaction management
- Query optimization
- Bulk operations

**Methods:**
- `create()`: Insert new record
- `get_by_id()`: Fetch by ID
- `update()`: Update record
- `delete()`: Delete record
- `get_all()`: List with filters
- `get_statistics()`: Aggregate data

**Example:**
```python
from app.repositories.news_repository import NewsRepository

repo = NewsRepository(db)
news = repo.get_by_id(123)
stats = repo.get_statistics()
```

---

### 5. **app/routers/** - API Endpoints

FastAPI route handlers organized by functionality.

#### `auth.py` - Authentication Routes
- `POST /pnl7a3d/login`: User login
- `POST /pnl7a3d/logout`: User logout
- `GET /pnl7a3d/`: Login page

#### `news.py` - News Routes
- `GET /news`: List news with filters
- `GET /news/{id}`: Get single news
- `PUT /news/{id}`: Update news
- `DELETE /news/{id}`: Delete news
- `POST /approve_translate/{id}`: Approve for translation
- `POST /final_approve/{id}`: Final approval
- `GET /stats`: Statistics

#### `admin.py` - Admin Routes
- `GET /pnl7a3d/dashboard`: Dashboard page
- `GET /pnl7a3d/advanced_crawl`: Advanced crawler page
- `POST /pnl7a3d/crawl_by_date`: Simple crawl
- `POST /pnl7a3d/advanced_crawl`: Advanced crawl
- `POST /pnl7a3d/publish_news`: Publish to Telegram
- `GET /pnl7a3d/logs`: View logs
- `GET /pnl7a3d/test_connection`: Test external services

---

### 6. **app/utils/** - Utility Functions

Reusable helper functions and classes.

#### `proxy.py` - Proxy Manager
- SOCKS5 proxy support
- Session management
- Automatic retry
- Connection pooling

#### `scoring.py` - News Scoring
- Multi-factor scoring algorithm
- Keyword matching
- Freshness calculation
- Relevance scoring

#### `logging.py` - Log Analyzer
- Log parsing and analysis
- Statistics generation
- Log filtering
- Search functionality

**Example:**
```python
from app.utils.scoring import calculate_news_score

score = calculate_news_score(
    title="Important News",
    text="Full article text...",
    published_date=datetime.now()
)
```

---

## 🔄 Request Flow

### Example: User Logs In

```
1. User submits login form
   ↓
2. Browser → POST /pnl7a3d/login
   ↓
3. routers/auth.py → login()
   ↓
4. services/auth.py → verify_credentials()
   ↓
5. services/auth.py → create_session()
   ↓
6. Response with session cookie
   ↓
7. Redirect to dashboard
```

### Example: Crawling News

```
1. User clicks "Crawl News"
   ↓
2. Browser → POST /pnl7a3d/crawl_by_date
   ↓
3. routers/admin.py → crawl_by_date()
   ↓
4. services/crawler.py → crawl_news()
   ↓
5. External API → Webz.io
   ↓
6. utils/scoring.py → calculate_score()
   ↓
7. repositories/news_repository.py → create()
   ↓
8. Database → Insert records
   ↓
9. Response → News count
```

---

## 🗄️ Database Schema

### News Table

```sql
CREATE TABLE news (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    thread_url TEXT,
    highlight_text TEXT,
    highlight_title TEXT,
    language VARCHAR(10),
    status VARCHAR(20) DEFAULT 'collected',
    score FLOAT DEFAULT 0.0,
    published DATETIME,
    translated_text TEXT,
    edited_farsi_text TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_status_score ON news(status, score DESC);
CREATE INDEX idx_language_status ON news(language, status);
CREATE INDEX idx_published_status ON news(published DESC, status);
CREATE INDEX idx_created_status ON news(created DESC, status);
```

---

## 🔐 Security Layers

### 1. Authentication
- Pre-hashed passwords (bcrypt)
- Secure session tokens (UUID4)
- Session expiration (24 hours)
- Cookie-based authentication

### 2. API Security
- Rate limiting (slowapi)
- Request validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection (FastAPI defaults)

### 3. Configuration Security
- Environment variables
- Secret key rotation
- Sensitive data in .env
- No hardcoded credentials

### 4. Network Security
- HTTPS support
- SOCKS5 proxy support
- Timeout configurations
- Connection retries

---

## 📊 Data Flow Diagrams

### News Collection Flow

```
External Source → Crawler → Scoring → Database
     (Webz.io)   (Filter)  (Rank)    (Store)
                     ↓
              Duplicate Check
                     ↓
              Status: COLLECTED
```

### Translation Flow

```
Database → Translator → Database
(status:   (Gemini AI   (status:
APPROVED)  or Google)   TRANSLATED)
```

### Publishing Flow

```
Database → Telegram → Database
(status:   (Bot API)  (status:
READY)               PUBLISHED)
```

---

## 🧪 Testing Strategy

### Unit Tests
- Test individual functions
- Mock external dependencies
- Test edge cases
- Fast execution

### Integration Tests
- Test component interactions
- Test database operations
- Test API endpoints
- Real database (test DB)

### End-to-End Tests
- Test complete workflows
- Test UI interactions
- Test with real services
- Performance testing

---

## 🚀 Deployment Options

### Option 1: Direct Deployment
```bash
python app/main.py
```

### Option 2: Docker
```bash
docker-compose up -d
```

### Option 3: Production Server
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 📈 Scalability Considerations

### Current Limitations
- SQLite (single-file database)
- In-memory sessions
- Single server instance

### Production Recommendations
1. **Database**: Migrate to PostgreSQL
2. **Sessions**: Use Redis for session storage
3. **Caching**: Implement Redis caching
4. **Load Balancing**: Use Nginx/HAProxy
5. **Task Queue**: Add Celery for background tasks
6. **Monitoring**: Add Prometheus + Grafana
7. **Logging**: Centralize with ELK stack

---

## 🔧 Configuration Management

### Environment Variables
All configuration via `.env` file:
- API keys
- Database URL
- Server settings
- Feature flags

### Config Validation
Pydantic validates all settings on startup:
- Required fields
- Type checking
- Value constraints
- Default values

---

## 📝 Coding Standards

### Python Style
- PEP 8 compliance
- Type hints
- Docstrings (Google style)
- Max line length: 88 (Black)

### Naming Conventions
- Classes: `PascalCase`
- Functions: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

### Documentation
- Module docstrings
- Function docstrings
- Inline comments for complex logic
- API endpoint descriptions

---

## 🎓 Learning Resources

### FastAPI
- [Official Docs](https://fastapi.tiangolo.com/)
- [Tutorial](https://fastapi.tiangolo.com/tutorial/)

### SQLAlchemy
- [Official Docs](https://docs.sqlalchemy.org/)
- [ORM Tutorial](https://docs.sqlalchemy.org/en/14/orm/tutorial.html)

### Pydantic
- [Official Docs](https://docs.pydantic.dev/)

---

## 🤝 Contributing

### Development Setup
1. Fork repository
2. Create feature branch
3. Make changes
4. Write tests
5. Submit pull request

### Code Review Process
1. Automated tests pass
2. Code review by maintainer
3. Documentation updated
4. Merge to main

---

## 📞 Support

For questions or issues:
- Read documentation first
- Check existing issues
- Create new issue with details
- Join community discussions

---

<div align="center">

**Last Updated:** 2024  
**Version:** 2.0.0  
**Maintainer:** IranBureau Team

</div>