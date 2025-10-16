#!/bin/bash

# Script to create complete project structure for News Management System v2.0
# Run this script in your project root directory

echo "🚀 Creating News Management System v2.0 Project Structure..."
echo ""

# Create main app directory structure
echo "📁 Creating directories..."

mkdir -p app/models
mkdir -p app/schemas
mkdir -p app/services
mkdir -p app/repositories
mkdir -p app/routers
mkdir -p app/utils
mkdir -p static
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p logs

echo "✅ Directories created"
echo ""

# Create __init__.py files
echo "📝 Creating __init__.py files..."

touch app/__init__.py
touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/services/__init__.py
touch app/repositories/__init__.py
touch app/routers/__init__.py
touch app/utils/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

echo "✅ __init__.py files created"
echo ""

# Create placeholder files (you'll fill these with actual code)
echo "📄 Creating placeholder Python files..."

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

# Core files
touch app/main.py
touch app/config.py
touch app/database.py
touch app/dependencies.py

echo "✅ Python files created"
echo ""

# Create configuration files
echo "⚙️  Creating configuration files..."

touch .env
touch .env.example
touch .gitignore
touch requirements.txt
touch setup.py
touch Dockerfile
touch docker-compose.yml
touch Makefile
touch README.md
touch MIGRATION.md

echo "✅ Configuration files created"
echo ""

# Create test files
echo "🧪 Creating test files..."

touch tests/unit/test_auth.py
touch tests/unit/test_scoring.py
touch tests/unit/test_translator.py
touch tests/integration/test_crawler.py
touch tests/integration/test_workflow.py

echo "✅ Test files created"
echo ""

# Display project structure
echo "📊 Project Structure:"
echo ""
tree -L 3 -I '__pycache__|*.pyc' || find . -type d -not -path '*/\.*' | sed 's|[^/]*/| |g'
echo ""

echo "✅ Project structure created successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Copy your HTML files to static/ directory"
echo "2. Fill in the .env file with your credentials"
echo "3. Copy the Python code to respective files"
echo "4. Run: pip install -r requirements.txt"
echo "5. Run: python setup.py"
echo "6. Run: python app/main.py"
echo ""
echo "🎉 Happy coding!"
