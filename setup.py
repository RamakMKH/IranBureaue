#!/usr/bin/env python3
"""
Setup and utility scripts for News Management System
"""
import os
import sys
import bcrypt


def generate_password_hash():
    """Generate bcrypt password hash"""
    print("\n" + "="*50)
    print("🔐 Password Hash Generator")
    print("="*50 + "\n")
    
    password = input("Enter password to hash: ")
    confirm = input("Confirm password: ")
    
    if password != confirm:
        print("❌ Passwords don't match!")
        sys.exit(1)
    
    if len(password) < 8:
        print("⚠️  Warning: Password is too short (minimum 8 characters recommended)")
    
    # استفاده مستقیم از bcrypt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    print("\n✅ Password hashed successfully!")
    print("\nAdd this to your .env file:")
    print(f"ADMIN_PASSWORD_HASH={hashed.decode('utf-8')}")
    print()


def generate_secret_key():
    """Generate secret key"""
    import secrets
    
    print("\n" + "="*50)
    print("🔑 Secret Key Generator")
    print("="*50 + "\n")
    
    key = secrets.token_urlsafe(32)
    
    print("✅ Secret key generated!")
    print("\nAdd this to your .env file:")
    print(f"SECRET_KEY={key}")
    print()


def generate_secret_path():
    """Generate random secret path"""
    import secrets
    import string
    
    print("\n" + "="*50)
    print("🎲 Secret Path Generator")
    print("="*50 + "\n")
    
    # Generate random alphanumeric string
    chars = string.ascii_lowercase + string.digits
    path = ''.join(secrets.choice(chars) for _ in range(12))
    
    print("✅ Secret path generated!")
    print("\nAdd this to your .env file:")
    print(f"SECRET_PATH={path}")
    print()
    print("⚠️  Keep this path secret! This will be your admin panel URL.")
    print(f"Example: https://yourdomain.com/{path}/")
    print()


def check_environment():
    """Check environment configuration"""
    print("\n" + "="*50)
    print("🔍 Environment Check")
    print("="*50 + "\n")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        "SECRET_KEY": "Secret key for sessions",
        "SECRET_PATH": "Secret path for admin panel",
        "ADMIN_USERNAME": "Admin username",
        "ADMIN_PASSWORD_HASH": "Hashed admin password",
        "WEBZ_API_KEYS": "Webz.io API keys",
        "TELEGRAM_BOT_TOKEN": "Telegram bot token",
        "TELEGRAM_CHANNEL": "Telegram channel"
    }
    
    all_good = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and value.strip():
            print(f"✅ {var}: OK")
        else:
            print(f"❌ {var}: MISSING ({description})")
            all_good = False
    
    optional_vars = {
        "GEMINI_API_KEYS": "Gemini AI (optional)",
        "SOCKS5_PROXY": "SOCKS5 Proxy (optional)",
        "APP_HOST": "Application host (default: 0.0.0.0)",
        "APP_PORT": "Application port (default: 8000)",
        "USE_HTTPS": "Enable HTTPS (default: false)",
        "SSL_CERT_PATH": "SSL certificate path",
        "SSL_KEY_PATH": "SSL private key path"
    }
    
    print("\nOptional variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value and value.strip():
            print(f"✅ {var}: Configured")
        else:
            print(f"⚪ {var}: Not configured ({description})")
    
    print()
    
    if all_good:
        print("✅ All required environment variables are set!")
    else:
        print("❌ Some required variables are missing. Please check your .env file.")
    
    return all_good


def init_database():
    """Initialize database"""
    print("\n" + "="*50)
    print("🗄️  Database Initialization")
    print("="*50 + "\n")
    
    try:
        # Import directly without going through config validation
        from sqlalchemy import create_engine
        from app.models.news import Base
        
        # Create engine
        engine = create_engine(
            'sqlite:///news.db',
            connect_args={'check_same_thread': False}
        )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database initialized successfully!")
        print("📊 Database file: news.db")
        
        # Verify tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📋 Tables created: {', '.join(tables)}")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_connections():
    """Test external connections"""
    print("\n" + "="*50)
    print("🔌 Connection Tests")
    print("="*50 + "\n")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # تنظیم پراکسی برای requests
    socks5_proxy = os.getenv("SOCKS5_PROXY")
    if socks5_proxy:
        os.environ['http_proxy'] = socks5_proxy
        os.environ['https_proxy'] = socks5_proxy
    
    # Test Telegram
    print("📱 Testing Telegram...")
    try:
        import subprocess
        import json
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if bot_token:
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            
            # استفاده از proxychains برای دور زدن محدودیت
            result = subprocess.run(
                ['proxychains', 'curl', '-s', url],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                try:
                    # پاک کردن خروجی proxychains از نتیجه
                    output = result.stdout
                    # پیدا کردن اولین { که شروع JSON است
                    json_start = output.find('{')
                    if json_start != -1:
                        json_output = output[json_start:]
                        bot_info = json.loads(json_output)
                        
                        if bot_info.get("ok"):
                            username = bot_info.get('result', {}).get('username', 'unknown')
                            print(f"✅ Telegram: Connected (@{username})")
                        else:
                            print("❌ Telegram: Invalid response")
                    else:
                        print("❌ Telegram: Could not parse response")
                except json.JSONDecodeError:
                    print("❌ Telegram: Invalid JSON response")
            else:
                print(f"❌ Telegram: Failed (Return code: {result.returncode})")
        else:
            print("⚠️  Telegram: No token configured")
    except FileNotFoundError:
        print("⚠️  Telegram: proxychains not found, skipping test")
    except subprocess.TimeoutExpired:
        print("❌ Telegram: Connection timeout")
    except Exception as e:
        print(f"❌ Telegram: Error - {e}")
    
    # Test Webz.io
    print("🌐 Testing Webz.io...")
    try:
        import requests
        api_keys = os.getenv("WEBZ_API_KEYS", "")
        keys_list = [k.strip() for k in api_keys.split(",") if k.strip()]
        
        if keys_list:
            proxies = {}
            socks5_proxy = os.getenv("SOCKS5_PROXY")
            if socks5_proxy:
                proxies = {
                    "http": socks5_proxy,
                    "https": socks5_proxy
                }
            
            url = f"https://api.webz.io/newsApiLite?token={keys_list[0]}&q=test&language=english&size=1"
            response = requests.get(url, timeout=10, proxies=proxies)
            
            if response.status_code == 200:
                print("✅ Webz.io: Connected")
            else:
                print(f"❌ Webz.io: Failed (Status: {response.status_code})")
        else:
            print("⚠️  Webz.io: No API keys configured")
    except Exception as e:
        print(f"❌ Webz.io: Error - {e}")
    
    # Test Translation
    print("🌍 Testing Translation...")
    try:
        import requests
        
        proxies = {}
        socks5_proxy = os.getenv("SOCKS5_PROXY")
        if socks5_proxy:
            proxies = {
                "http": socks5_proxy,
                "https": socks5_proxy
            }
        
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "en",
            "tl": "fa",
            "dt": "t",
            "q": "Hello"
        }
        response = requests.get(url, params=params, timeout=10, proxies=proxies)
        
        if response.status_code == 200:
            print("✅ Translation: Working")
        else:
            print(f"❌ Translation: Failed (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Translation: Error - {e}")
    
    print()


def create_env_file():
    """Create .env file from template"""
    print("\n" + "="*50)
    print("📝 Create .env File")
    print("="*50 + "\n")
    
    if os.path.exists(".env"):
        overwrite = input(".env file already exists. Overwrite? (y/N): ")
        if overwrite.lower() != 'y':
            print("Cancelled.")
            return
    
    try:
        with open(".env.example", "r") as f:
            template = f.read()
        
        with open(".env", "w") as f:
            f.write(template)
        
        print("✅ .env file created from template")
        print("⚠️  Please edit .env and fill in your credentials!")
    except Exception as e:
        print(f"❌ Failed to create .env: {e}")


def show_security_tips():
    """Show security best practices"""
    print("\n" + "="*50)
    print("🔐 Security Best Practices")
    print("="*50 + "\n")
    
    tips = [
        "1. Use a strong SECRET_KEY (32+ characters)",
        "2. Generate a random SECRET_PATH (not 'admin' or 'dashboard')",
        "3. Never commit .env file to git",
        "4. Use strong admin password (12+ characters)",
        "5. Enable HTTPS in production",
        "6. Regularly rotate API keys",
        "7. Keep dependencies updated",
        "8. Monitor logs for suspicious activity",
        "9. Use PostgreSQL in production",
        "10. Regular database backups"
    ]
    
    for tip in tips:
        print(f"  {tip}")
    
    print()


def main():
    """Main menu"""
    while True:
        print("\n" + "="*50)
        print("📰 News Management System - Setup Utility")
        print("="*50)
        print("\n1. Generate password hash")
        print("2. Generate secret key")
        print("3. Generate secret path")
        print("4. Create .env file from template")
        print("5. Check environment configuration")
        print("6. Initialize database")
        print("7. Test connections")
        print("8. Run all checks")
        print("9. Show security tips")
        print("0. Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == "1":
            generate_password_hash()
        elif choice == "2":
            generate_secret_key()
        elif choice == "3":
            generate_secret_path()
        elif choice == "4":
            create_env_file()
        elif choice == "5":
            check_environment()
        elif choice == "6":
            init_database()
        elif choice == "7":
            test_connections()
        elif choice == "8":
            print("\n🔍 Running all checks...\n")
            if check_environment():
                init_database()
                test_connections()
            else:
                print("\n❌ Fix environment issues first!")
        elif choice == "9":
            show_security_tips()
        elif choice == "0":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
