#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path

def activate_venv():
    """Activate virtual environment"""
    venv_path = Path(__file__).parent / "venv"
    
    if sys.platform == "win32":
        activate_script = venv_path / "Scripts" / "activate.bat"
        python_executable = venv_path / "Scripts" / "python.exe"
    else:
        activate_script = venv_path / "bin" / "activate"
        python_executable = venv_path / "bin" / "python"
    
    if not python_executable.exists():
        print("❌ Virtual environment not found!")
        print("Please run: python3 -m venv venv")
        print("Then: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)")
        print("And: pip install -r requirements.txt")
        return None
        
    return str(python_executable)

def check_env_file():
    """Check if .env file exists"""
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Please create .env file with:")
        print("BOT_TOKEN=your_telegram_bot_token_here")
        print("ADMIN_CHAT_ID=your_admin_chat_id_here")
        print("DATABASE_URL=sqlite:///./bookings.db")
        return False
    return True

def install_requirements():
    """Install requirements if needed"""
    python_exe = activate_venv()
    if not python_exe:
        return False
        
    try:
        subprocess.run([python_exe, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        return False

def run_bot():
    """Run the Telegram bot"""
    if not check_env_file():
        return
        
    python_exe = activate_venv()
    if not python_exe:
        return
        
    # Load environment variables
    env_file = Path(__file__).parent / ".env"
    env_vars = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    
    # Set environment variables
    env = os.environ.copy()
    env.update(env_vars)
    
    try:
        print("🤖 Starting Telegram bot...")
        subprocess.run([python_exe, "bot.py"], env=env, cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n👋 Bot stopped!")
    except Exception as e:
        print(f"❌ Error running bot: {e}")

def run_api():
    """Run the FastAPI server"""
    python_exe = activate_venv()
    if not python_exe:
        return
        
    try:
        print("🚀 Starting FastAPI server on http://localhost:8000")
        subprocess.run([python_exe, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"], 
                      cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n👋 API server stopped!")
    except Exception as e:
        print(f"❌ Error running API server: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python run.py install  - Install requirements")
        print("  python run.py bot      - Run Telegram bot")
        print("  python run.py api      - Run FastAPI server")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "install":
        install_requirements()
    elif command == "bot":
        run_bot()
    elif command == "api":
        run_api()
    else:
        print(f"Unknown command: {command}")