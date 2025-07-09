#!/usr/bin/env python3
"""
Script to create standalone .exe for Stockmarket Clone game
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path
import time


def kill_running_exe():
    """Kill any running instances of our game"""
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'StockmarketClone' in proc.info['name']:
                    proc.kill()
                    print(f"✓ Killed running process: {proc.info['name']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except ImportError:
        print("✗ psutil not found, skipping process cleanup")


def create_exe():
    """Create executable using PyInstaller"""
    # Check for required packages
    packages = ['pyinstaller', 'psutil']
    for package in packages:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} not found. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    # Kill any running instances
    kill_running_exe()

    # Clean up previous builds
    for path in ['build', 'dist']:
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"✓ Cleaned {path} directory")

    # PyInstaller command
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name", "StockmarketClone",
        "--add-data", "templates;templates",
        "--add-data", "static;static",
        "--hidden-import", "eventlet",
        "--hidden-import", "eventlet.hubs.epolls",
        "--hidden-import", "eventlet.hubs.kqueue",
        "--hidden-import", "eventlet.hubs.selects",
        "--hidden-import", "eventlet.greenthread",
        "--hidden-import", "eventlet.websocket",
        "--hidden-import", "eventlet.wsgi",
        "--hidden-import", "dns",
        "--hidden-import", "dns.resolver",
        "--hidden-import", "dns.rdtypes",
        "--hidden-import", "dns.exception",
        "--hidden-import", "socketio",
        "--hidden-import", "engineio",
        "--hidden-import", "flask_socketio",
        "--hidden-import", "socketio.async_drivers.eventlet",
        "--collect-all", "eventlet",
        "--collect-all", "dns",
        "--collect-all", "socketio",
        "--collect-all", "engineio",
        "--collect-all", "flask_socketio",
        "app_bundled.py"
    ]

    # Run PyInstaller
    print("Building executable...")
    subprocess.check_call(cmd)

    # Verify the build
    exe_path = Path("dist/StockmarketClone.exe")
    if exe_path.exists():
        print(f"✓ Successfully created {exe_path}")
        return str(exe_path)
    else:
        print("✗ Failed to create executable")
        return None

    # Run PyInstaller
    print("Building executable...")
    subprocess.check_call(cmd)

    # Verify the build
    exe_path = Path("dist/StockmarketClone.exe")
    if exe_path.exists():
        print(f"✓ Successfully created {exe_path}")
        return str(exe_path)
    else:
        print("✗ Failed to create executable")
        return None


def main():
    """Main entry point"""
    exe_path = create_exe()
    if exe_path:
        print("\nBuild successful! You can now run StockmarketClone.exe")
        print(f"Executable location: {exe_path}")
    else:
        print("\nBuild failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()

    # Run PyInstaller
    print("Building executable...")
    subprocess.check_call(cmd)

    # Verify the build
    exe_path = Path("dist/StockmarketClone.exe")
    if exe_path.exists():
        print(f"✓ Successfully created {exe_path}")
        return str(exe_path)
    else:
        print("✗ Failed to create executable")
        return None


def main():
    """Main entry point"""
    exe_path = create_exe()
    if exe_path:
        print("\nBuild successful! You can now run StockmarketClone.exe")
        print(f"Executable location: {exe_path}")
    else:
        print("\nBuild failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
        "--collect-all=socketio",
        "--collect-all=engineio",
        "app_prod.py",  # Use production version with eventlet
    ]

    print("🔨 Building executable...")
    print(f"Command: {' '.join(cmd)}")

    try:
        # Run PyInstaller
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Build completed successfully!")

        # Check if exe was created
        exe_path = Path("dist/StockmarketClone.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"✓ Executable created: {exe_path}")
            print(f"✓ File size: {size_mb:.1f} MB")

            # Create a simple launcher script
            create_launcher()

            print("\n🎉 SUCCESS!")
            print(f"Your game is ready: {exe_path.absolute()}")
            print("\nTo distribute the game:")
            print("1. Copy the StockmarketClone.exe file to any Windows computer")
            print("2. Double-click to run")
            print("3. Open browser to http://localhost:5000")
            print(
                "\nNote: The game will open a local web server that you access through your browser."
            )

        else:
            print("✗ Executable not found in dist folder")

    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        print("Error output:")
        print(e.stderr)
        return False

    return True


def create_launcher():
    """Create a simple batch file to explain how to use the exe"""
    launcher_content = """@echo off
title Stockmarket Clone - C64 Style Game
echo ========================================
echo    Stockmarket Clone - C64 Style Game
echo ========================================
echo.
echo This game recreates the classic C64 "Stockmarket 1982" game
echo as a modern web application with multiplayer support!
echo.
echo Instructions:
echo 1. The game will start a local web server
echo 2. Your browser will open automatically to http://localhost:5000
echo 3. If browser doesn't open, manually go to: http://localhost:5000
echo 4. Other players can join from the network at: http://[your-ip]:5000
echo.
echo To stop the game: Close this window or press Ctrl+C
echo ========================================
echo.
pause

StockmarketClone.exe
"""

    with open("dist/Start_Game.bat", "w") as f:
        f.write(launcher_content)

    print("✓ Created Start_Game.bat launcher")


if __name__ == "__main__":
    print("🚀 Creating standalone executable for Stockmarket Clone...")
    print("=" * 60)

    if create_exe():
        print("\n🎮 Ready to play! Run the .exe file to start the game.")
    else:
        print("\n❌ Build failed. Check the error messages above.")
