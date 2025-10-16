#!/usr/bin/env python3
"""
Setup and utility scripts for News Management System
"""
import os
import sys
from passlib.context import CryptContext


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
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_context.hash(password)
    
    print("\n✅ Password hashed successfully!")
    print("\nAdd this to your .env file:")
    print(f"ADMIN_PASSWORD_HASH={hashed}")
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


def check_environment():
    """Check environment configuration"""
    print("\n" + "="*50)
    print("🔍 Environment Check")
    print("="*50 + "\n")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        "SECRET_KEY": "Secret key for sessions",
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
        "SOCKS5_PROXY": "SOCKS5 Proxy (optional)"
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
        from database import init_database
        init_database()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)


def test_connections():
    """Test external connections"""
    print("\n" + "="*50)
    print("🔌 Connection Tests")
    print("="*50 + "\n")
    
    # Test Telegram
    try:
        from services.telegram import telegram_service
        if telegram_service.test_connection():
            print("✅ Telegram: Connected")
        else:
            print("❌ Telegram: Failed")
    except Exception as e:
        print(f"❌ Telegram: Error - {e}")
    
    # Test Webz.io
    try:
        from config import settings
        from utils.proxy import proxy_manager
        import requests
        
        session = proxy_manager.create_session(timeout=10)
        url = f"https://api.webz.io/newsApiLite?token={settings.WEBZ_API_KEYS[0]}&q=test"
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Webz.io: Connected")
        else:
            print(f"❌ Webz.io: Failed (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Webz.io: Error - {e}")
    
    # Test Translation
    try:
        from services.translator import translation_service
        test_result = translation_service.translate("Hello world", "fa")
        if test_result:
            print("✅ Translation: Working")
        else:
            print("❌ Translation: Failed")
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


def main():
    """Main menu"""
    while True:
        print("\n" + "="*50)
        print("📰 News Management System - Setup Utility")
        print("="*50)
        print("\n1. Generate password hash")
        print("2. Generate secret key")
        print("3. Create .env file from template")
        print("4. Check environment configuration")
        print("5. Initialize database")
        print("6. Test connections")
        print("7. Run all checks")
        print("0. Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == "1":
            generate_password_hash()
        elif choice == "2":
            generate_secret_key()
        elif choice == "3":
            create_env_file()
        elif choice == "4":
            check_environment()
        elif choice == "5":
            init_database()
        elif choice == "6":
            test_connections()
        elif choice == "7":
            print("\n🔍 Running all checks...\n")
            if check_environment():
                init_database()
                test_connections()
            else:
                print("\n❌ Fix environment issues first!")
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
