#!/bin/bash

# ============================================
# create_structure.sh
# Automatic Project Structure Creator
# News Management System v2.0
# ============================================

echo "🏗️  Creating News Management System Structure..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

# ============================================
# Create Directory Structure
# ============================================

print_info "Creating directories..."

# Main app directory
mkdir -p app/{models,schemas,services,repositories,routers,utils}
mkdir -p static
mkdir -p tests/{unit,integration}

print_status "Directories created"

# ============================================
# Create __init__.py Files
# ============================================

print_info "Creating __init__.py files..."

# Root app
cat > app/__init__.py << 'EOF'
"""
News Management System
Main application package
"""
__version__ = "2.0.0"
EOF

# Models
cat > app/models/__init__.py << 'EOF'
"""
Database models
"""
from .news import News, NewsStatus, Base

__all__ = ["News", "NewsStatus", "Base"]
EOF

# Schemas
cat > app/schemas/__init__.py << 'EOF'
"""
Pydantic schemas for request/response validation
"""
from .news import (
    AuthRequest,
    CrawlRequest,
    AdvancedCrawlRequest,
    NewsResponse,
    StatsResponse,
    CrawlResponse,
    ConnectionTestResponse
)

__all__ = [
    "AuthRequest",
    "CrawlRequest",
    "AdvancedCrawlRequest",
    "NewsResponse",
    "StatsResponse",
    "CrawlResponse",
    "ConnectionTestResponse"
]
EOF

# Services
cat > app/services/__init__.py << 'EOF'
"""
Business logic services
"""
from .auth import auth_service
from .crawler import crawler_service
from .translator import translation_service
from .telegram import telegram_service

__all__ = [
    "auth_service",
    "crawler_service",
    "translation_service",
    "telegram_service"
]
EOF

# Repositories
cat > app/repositories/__init__.py << 'EOF'
"""
Data access layer - Repository pattern
"""
from .news_repository import NewsRepository

__all__ = ["NewsRepository"]
EOF

# Routers
cat > app/routers/__init__.py << 'EOF'
"""
API route handlers
"""
from . import auth, news, admin

__all__ = ["auth", "news", "admin"]
EOF

# Utils
cat > app/utils/__init__.py << 'EOF'
"""
Utility functions and helpers
"""
from .proxy import proxy_manager
from .scoring import calculate_news_score
from .logging import LogAnalyzer

__all__ = [
    "proxy_manager",
    "calculate_news_score",
    "LogAnalyzer"
]
EOF

# Tests
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

print_status "__init__.py files created"

# ============================================
# Create Placeholder Files
# ============================================

print_info "Creating placeholder Python files..."

# Core files
touch app/main.py
touch app/config.py
touch app/database.py
touch app/dependencies.py

# Models
touch app/models/news.py

# Schemas
touch app/schemas/news.py

# Services
touch app/services/auth.py
touch app/services/crawler.py
touch app/services/translator.py
touch app/services/telegram.py

# Repositories
touch app/repositories/news_repository.py

# Routers
touch app/routers/auth.py
touch app/routers/news.py
touch app/routers/admin.py

# Utils
touch app/utils/proxy.py
touch app/utils/scoring.py
touch app/utils/logging.py

print_status "Python files created"

# ============================================
# Create Static HTML Files
# ============================================

print_info "Creating static HTML files..."

touch static/index.html
touch static/dashboard.html
touch static/advanced_crawl.html
touch static/logs.html

print_status "HTML files created"

# ============================================
# Create Configuration Files
# ============================================

print_info "Creating configuration files..."

# .env.example (if not exists)
if [ ! -f .env.example ]; then
    print_warning ".env.example not found - please create it manually"
else
    print_status ".env.example exists"
fi

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.so
venv/
ENV/
.venv

# Database
*.db
*.sqlite
news.db

# Logs
*.log
webz.log

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
.DS_Store

# Testing
.pytest_cache/
.coverage

# Temporary
*.tmp
.cache/
EOF

print_status ".gitignore created"

# ============================================
# Verify Structure
# ============================================

print_info "Verifying structure..."

# Count Python files
PYTHON_FILES=$(find app -name "*.py" | wc -l)
HTML_FILES=$(find static -name "*.html" | wc -l)
INIT_FILES=$(find app -name "__init__.py" | wc -l)

echo ""
print_info "Structure Summary:"
echo "  📄 Python files: $PYTHON_FILES"
echo "  🌐 HTML files: $HTML_FILES"
echo "  📦 __init__.py files: $INIT_FILES"
echo ""

# ============================================
# Display Tree
# ============================================

if command -v tree &> /dev/null; then
    print_info "Project Structure:"
    tree -L 3 -I '__pycache__|*.pyc|venv' --dirsfirst
else
    print_warning "Install 'tree' command for better visualization"
fi

echo ""
print_status "Structure created successfully!"
echo ""
print_info "Next Steps:"
echo "  1. Copy file contents from artifacts"
echo "  2. Create .env from .env.example"
echo "  3. pip install -r requirements.txt"
echo "  4. python setup.py (for initial setup)"
echo "  5. python app/main.py (to run)"
echo ""
print_info "Need help? Check README.md and FILE_CHECKLIST.md"
echo ""