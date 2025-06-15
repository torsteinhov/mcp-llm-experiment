#!/usr/bin/env python3
"""
Flight Tracker Launcher Script
Complete launcher that checks dependencies and starts the web application.
"""

import subprocess
import sys
import os
from pathlib import Path
import webbrowser
import time

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        ('flask', 'Flask'),
        ('folium', 'folium'), 
        ('requests', 'requests'),
        ('aiohttp', 'aiohttp')
    ]
    
    missing_packages = []
    
    print("🔍 Checking Python packages...")
    for package_name, install_name in required_packages:
        try:
            __import__(package_name)
            print(f"✅ {install_name} is installed")
        except ImportError:
            missing_packages.append(install_name)
            print(f"❌ {install_name} is missing")
    
    return missing_packages

def install_dependencies():
    """Install missing dependencies."""
    print("\n🔧 Installing web application dependencies...")
    
    try:
        # Install from requirements file if it exists
        if Path("requirements-web.txt").exists():
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements-web.txt"
            ], check=True)
        else:
            # Install individual packages
            packages = ["flask>=2.3.0", "folium>=0.14.0", "requests>=2.31.0", "aiohttp>=3.8.0", "python-dotenv>=0.19.0"]
            subprocess.run([
                sys.executable, "-m", "pip", "install"
            ] + packages, check=True)
        
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_env_file():
    """Check if .env file exists and has required API key."""
    env_path = Path(".env")
    
    if not env_path.exists():
        print("❌ .env file not found!")
        print("\n🔧 Creating .env file template...")
        with open(".env", "w") as f:
            f.write("# Add your AviationStack API key here\n")
            f.write("# Get free API key at: https://aviationstack.com/signup/free\n")
            f.write("AVIATIONSTACK_API_KEY=your_api_key_here\n")
        
        print("📝 .env file created. Please:")
        print("1. Get your free API key from: https://aviationstack.com/signup/free")
        print("2. Edit .env file and replace 'your_api_key_here' with your actual API key")
        print("3. Run this script again")
        return False
    
    # Check if API key is set
    try:
        with open(".env", "r") as f:
            content = f.read()
            if "your_api_key_here" in content:
                print("❌ AviationStack API key not configured in .env file!")
                print("📝 Please edit .env file and replace 'your_api_key_here' with your actual API key")
                return False
            elif "AVIATIONSTACK_API_KEY=" not in content:
                print("❌ AVIATIONSTACK_API_KEY not found in .env file!")
                print("📝 Please add: AVIATIONSTACK_API_KEY=your_actual_api_key")
                return False
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False
    
    print("✅ .env file configured")
    return True

def check_mcp_server():
    """Check if MCP server files exist."""
    server_path = Path("src/mcp_server/server.py")
    
    if not server_path.exists():
        print("❌ MCP server not found at src/mcp_server/server.py")
        print("📝 Please ensure your MCP server is properly set up")
        return False
    
    print("✅ MCP server found")
    return True

def check_flight_tracker_app():
    """Check if the main flight tracker app exists."""
    app_path = Path("flight_tracker_app.py")
    
    if not app_path.exists():
        print("❌ flight_tracker_app.py not found!")
        print("📝 Please ensure flight_tracker_app.py is in the current directory")
        return False
    
    print("✅ flight_tracker_app.py found")
    return True

def start_web_app():
    """Start the Flask web application."""
    print("\n🚀 Starting Flight Tracker Web Application...")
    print("📍 The application will open at: http://localhost:5000")
    print("🔄 Starting server...")
    print("📝 To stop the server, press Ctrl+C")
    
    try:
        # Open browser after a short delay
        def open_browser():
            time.sleep(3)
            try:
                webbrowser.open('http://localhost:5000')
                print("🌐 Opening browser...")
            except Exception as e:
                print(f"⚠️ Could not open browser automatically: {e}")
                print("📝 Please manually open: http://localhost:5000")
        
        import threading
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Start the Flask app
        subprocess.run([sys.executable, "flight_tracker_app.py"], check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start web application: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main launcher function."""
    print("🛫 FLIGHT TRACKER WEB APPLICATION LAUNCHER")
    print("=" * 50)
    
    # Check current directory
    current_dir = Path.cwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Not in the MCP project directory!")
        print("📝 Please navigate to: C:\\Repositories\\Privat\\mcp-llm-experiment")
        print("📝 Then run this script again")
        input("\nPress Enter to exit...")
        return
    
    print("\n🔍 Checking system requirements...")
    
    # Check all requirements
    checks = [
        ("MCP Server", check_mcp_server),
        ("Flight Tracker App", check_flight_tracker_app),
        ("Environment File", check_env_file),
    ]
    
    for check_name, check_func in checks:
        print(f"\n📋 Checking {check_name}...")
        if not check_func():
            print(f"❌ {check_name} check failed!")
            input("Press Enter to exit...")
            return
    
    # Check dependencies
    print(f"\n📋 Checking Dependencies...")
    missing = check_dependencies()
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        response = input("🔧 Install missing dependencies? (y/n): ")
        
        if response.lower() in ['y', 'yes']:
            if not install_dependencies():
                print("❌ Failed to install dependencies!")
                input("Press Enter to exit...")
                return
            
            # Re-check dependencies after installation
            print("\n🔍 Re-checking dependencies...")
            missing_after = check_dependencies()
            if missing_after:
                print(f"❌ Still missing: {', '.join(missing_after)}")
                input("Press Enter to exit...")
                return
        else:
            print("❌ Cannot start without required dependencies")
            input("Press Enter to exit...")
            return
    
    print("\n✅ All requirements satisfied!")
    print("\n🎯 READY TO LAUNCH!")
    print("📝 The web application will:")
    print("   - Start a local web server on http://localhost:5000")
    print("   - Open your default browser automatically")
    print("   - Display an interactive flight tracking interface")
    print("   - Connect to your MCP server for real-time data")
    
    input("\nPress Enter to start the Flight Tracker...")
    
    # Start the web application
    try:
        start_web_app()
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Application error: {e}")
    finally:
        print("\n👋 Thank you for using Flight Tracker!")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()