# 📰 News Management System v2.0

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)

**A professional news crawling, translation, and publishing system with automated workflow**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Documentation](#-documentation) • [Support](#-support)

</div>

---

## 🎯 Overview

News Management System is a comprehensive solution for collecting, translating, and publishing international news articles. Built with FastAPI and modern Python practices, it provides an intelligent workflow from news collection to Telegram channel publication.

### 🌟 Key Highlights

- 🕷️ **Intelligent Crawler**: Collects news from Webz.io API with duplicate detection
- 🤖 **AI Translation**: Uses Gemini AI for high-quality Persian translation
- 📱 **Telegram Publishing**: Automated posting to Telegram channels
- 🎯 **Smart Scoring**: Priority-based scoring algorithm
- 🔐 **Secure Authentication**: Session-based auth with bcrypt
- 📊 **Admin Dashboard**: Full-featured web interface
- 🌍 **Multi-language**: Supports 10+ languages
- 🔄 **Automated Workflow**: Scheduled crawling and publishing

---

## ✨ Features

### News Collection
- ✅ Automated news crawling from Webz.io
- ✅ Advanced filtering (date range, keywords, categories)
- ✅ Duplicate detection using fuzzy matching
- ✅ Intelligent priority scoring
- ✅ Multi-language support

### Translation
- ✅ AI-powered translation (Gemini AI)
- ✅ Google Translate fallback
- ✅ Content summarization
- ✅ Quality improvements

### Publishing
- ✅ Telegram channel integration
- ✅ Automated scheduling
- ✅ Manual approval workflow
- ✅ Message formatting and optimization

### Administration
- ✅ Web-based dashboard
- ✅ User authentication
- ✅ Real-time logging
- ✅ Statistics and analytics
- ✅ System monitoring

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Routers  │  │ Services │  │Repository│             │
│  │  (API)   │─▶│ (Logic)  │─▶│  (Data)  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                      │              │                    │
│                      ▼              ▼                    │
│              ┌──────────┐    ┌──────────┐              │
│              │ External │    │ Database │              │
│              │   APIs   │    │ (SQLite) │              │
│              └──────────┘    └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip package manager
- (Optional) PostgreSQL for production
- Valid API keys (Webz.io, Telegram, Gemini)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/YourUsername/IranBureau.git
cd IranBureau
```

2. **Create virtual environment**

```bash
python -m venv venv

# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment**

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

5. **Generate password hash**

```bash
python setup.py
# Choose option 1: Generate password hash
# Copy the hash to .env ADMIN_PASSWORD_HASH
```

6. **Initialize database**

```bash
python setup.py
# Choose option 5: Initialize database
```

7. **Test connections**

```bash
python setup.py
# Choose option 6: Test connections
```

8. **Run the application**

```bash
python app/main.py
```

9. **Access the dashboard**

```
https://dsh.kaliroot.cf:2053/pnl7a3d/
```

---

## 📖 Usage

### Basic Workflow

1. **Login** to admin panel
2. **Crawl** news articles (manual or scheduled)
3. **Review** collected articles
4. **Approve** for translation
5. **Review** translated content
6. **Approve** for publishing
7. **Publish** to Telegram (manual or automatic)

### Manual Crawl

```bash
# Via Dashboard
1. Go to Dashboard
2. Select date and language
3. Click "Crawl News"

# Via API
curl -X POST https://dsh.kaliroot.cf:2053/pnl7a3d/crawl_by_date \
  -H "Content-Type: application/json" \
  -d '{"date": "2024-01-15", "language": "english"}'
```

### Advanced Crawl

```bash
# Use the Advanced Crawl page for:
- Date range selection
- Keyword filtering
- Custom limits
- Multiple languages
```

---

## ⚙️ Configuration

### Environment Variables

Key variables in `.env`:

```bash
# Security
SECRET_KEY=your-secret-key-32-chars-min
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$...

# API Keys
WEBZ_API_KEYS=key1,key2,key3
GEMINI_API_KEYS=key1,key2
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHANNEL=@YourChannel

# Optional
SOCKS5_PROXY=socks5://host:port
```

### Database Configuration

**Development (SQLite - Default):**
```bash
DATABASE_URL=sqlite:///news.db
```

**Production (PostgreSQL - Recommended):**
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/newsdb
```

---

## 📊 API Documentation

Once running, visit:

- **Swagger UI**: https://dsh.kaliroot.cf:2053/docs
- **ReDoc**: https://dsh.kaliroot.cf:2053/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/pnl7a3d/login` | POST | Login |
| `/pnl7a3d/dashboard` | GET | Main dashboard |
| `/news` | GET | Get news list |
| `/pnl7a3d/crawl_by_date` | POST | Crawl news |
| `/pnl7a3d/publish_news` | POST | Publish news |
| `/stats` | GET | Get statistics |

---

## 🛠️ Development

### Project Structure

```
IranBureau/
├── app/
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   ├── dependencies.py      # FastAPI dependencies
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── repositories/        # Data access
│   ├── routers/             # API routes
│   └── utils/               # Utilities
├── static/                  # Frontend files
├── tests/                   # Test suite
├── requirements.txt         # Dependencies
├── setup.py                 # Setup utility
└── .env                     # Configuration
```

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

---

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Manual Docker Build

```bash
# Build image
docker build -t news-system:latest .

# Run container
docker run -d -p 2053:2053 \
  --env-file .env \
  --name news-system \
  news-system:latest
```

---

## 📈 Monitoring & Maintenance

### Health Check

```bash
curl https://dsh.kaliroot.cf:2053/pnl7a3d/health
```

### View Logs

```bash
# Via dashboard
https://dsh.kaliroot.cf:2053/pnl7a3d/logs_page

# Via file
tail -f webz.log
```

### Database Backup

```bash
# SQLite backup
cp news.db news_backup_$(date +%Y%m%d).db

# PostgreSQL backup
pg_dump newsdb > backup_$(date +%Y%m%d).sql
```

### Cleanup Old News

```bash
# Via API (dry run first)
curl -X POST "https://dsh.kaliroot.cf:2053/pnl7a3d/cleanup_old_news?days=90&dry_run=true"
```

---

## 🔐 Security Best Practices

1. ✅ Always use HTTPS in production
2. ✅ Keep SECRET_KEY secure (32+ characters)
3. ✅ Never commit `.env` to git
4. ✅ Use strong admin passwords
5. ✅ Regularly rotate API keys
6. ✅ Monitor logs for suspicious activity
7. ✅ Keep dependencies updated
8. ✅ Enable firewall rules
9. ✅ Use PostgreSQL in production
10. ✅ Regular database backups

---

## 🐛 Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Ensure all __init__.py files exist
find app -type d -exec touch {}/__init__.py \;
```

**2. Database Errors**
```bash
# Reset database
rm news.db
python setup.py  # Option 5
```

**3. Proxy Connection Issues**
```bash
# Test proxy
python setup.py  # Option 6
```

**4. Password Hash Issues**
```bash
# Regenerate hash
python setup.py  # Option 1
```

**5. Telegram Connection Failed**
```bash
# Check bot token and channel ID
# Verify proxy settings if used
# Test connection via setup.py
```

---

## 📚 Documentation

- **[MIGRATION.md](MIGRATION.md)**: Upgrade from v1.0 to v2.0
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)**: Detailed structure
- **[API Documentation](https://dsh.kaliroot.cf:2053/docs)**: Swagger UI

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Write tests for new features
- Update documentation
- Use type hints
- Add docstrings

---

## 📝 Changelog

### v2.0.0 (2024)
- ✨ Complete refactoring with clean architecture
- ✨ Repository pattern implementation
- ✨ Enhanced security with pre-hashed passwords
- ✨ Improved logging and monitoring
- ✨ Docker support
- ✨ Advanced crawl with date ranges
- ✨ Better error handling
- ✨ Comprehensive documentation

### v1.0.0 (2023)
- 🎉 Initial release
- Basic crawling and publishing

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI** - Modern web framework
- **Webz.io** - News API provider
- **Google Gemini AI** - Translation service
- **Telegram** - Publishing platform
- **SQLAlchemy** - Database ORM

---

## 📞 Support

### Get Help

- 📧 Email: support@iranbureau.com
- 💬 Telegram: [@IranBureau](https://t.me/IranBureau)
- 🐛 Issues: [GitHub Issues](https://github.com/YourUsername/IranBureau/issues)
- 📖 Documentation: [Wiki](https://github.com/YourUsername/IranBureau/wiki)

### Reporting Bugs

Please include:
1. Description of the issue
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. System information
6. Log files (if applicable)

---

## 🌟 Star History

If you find this project useful, please consider giving it a ⭐!

[![Star History Chart](https://api.star-history.com/svg?repos=YourUsername/IranBureau&type=Date)](https://star-history.com/#YourUsername/IranBureau&Date)

---

## 📊 Statistics

- **Total Lines of Code**: ~3,500
- **Files**: 25+
- **Languages**: Python, HTML, JavaScript
- **Test Coverage**: TBD
- **Documentation**: Comprehensive

---

<div align="center">

**Made with ❤️ by IranBureau Team**

[Website](https://iranbureau.com) • [GitHub](https://github.com/YourUsername/IranBureau) • [Telegram](https://t.me/IranBureau)

**Version 2.0.0** | **2024** | **MIT License**

</div>
