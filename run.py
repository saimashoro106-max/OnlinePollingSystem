#!/usr/bin/env python3
"""
Easy Launch Script for AI Polling System
This script checks dependencies and starts the application
"""

import sys
import os
import subprocess


def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def check_dependencies():
    """Check if all required packages are installed"""
    print("\nChecking dependencies...")
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'werkzeug'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing_packages.append(package)

    if missing_packages:
        print("\n⚠️  Missing packages detected!")
        print("\nInstall them with:")
        print("  pip install -r requirements.txt")
        response = input("\nWould you like to install them now? (y/n): ")
        if response.lower() == 'y':
            try:
                print("\nInstalling dependencies...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
                print("\n✓ Dependencies installed successfully!")
                return True
            except subprocess.CalledProcessError:
                print("\n❌ Failed to install dependencies")
                return False
        else:
            return False

    print("✓ All dependencies installed")
    return True


def check_directories():
    """Check and create required directories"""
    print("\nChecking directories...")
    directories = [
        'static/uploads',
        'static/uploads/profiles',
        'static/uploads/polls',
        'templates'
    ]

    for directory in directories:
        if not os.path.exists(directory):
            print(f"Creating {directory}...")
            os.makedirs(directory, exist_ok=True)
        print(f"✓ {directory}")

    return True


def check_database():
    """Check if database exists"""
    print("\nChecking database...")
    if not os.path.exists('polling_system.db'):
        print("❌ Database not found!")
        print("\nDatabase needs to be initialized.")
        response = input("Would you like to initialize it now with sample data? (y/n): ")
        if response.lower() == 'y':
            try:
                print("\nInitializing database...")
                subprocess.check_call([sys.executable, 'init_db.py', '--with-samples'])
                print("\n✓ Database initialized successfully!")
                return True
            except subprocess.CalledProcessError:
                print("\n❌ Failed to initialize database")
                return False
            except FileNotFoundError:
                print("\n❌ init_db.py not found!")
                print("Please make sure all files are in the correct location.")
                return False
        else:
            print("\nYou can initialize the database later by running:")
            print("  python init_db.py --with-samples")
            return False
    else:
        print("✓ Database exists")
        return True


def check_templates():
    """Check if template files exist"""
    print("\nChecking template files...")
    required_templates = [
        'base.html',
        'index.html',
        'login.html',
        'register.html',
        'create_poll.html',
        'view_poll.html',
        'profile.html',
        'leaderboard.html',
        'admin_dashboard.html'
    ]

    missing_templates = []
    for template in required_templates:
        template_path = os.path.join('templates', template)
        if os.path.exists(template_path):
            print(f"✓ {template}")
        else:
            print(f"❌ {template} (missing)")
            missing_templates.append(template)

    if missing_templates:
        print("\n⚠️  Some template files are missing!")
        print("Please ensure all template files are in the templates/ folder")
        return False

    return True


def start_application():
    """Start the Flask application"""
    print("\n" + "=" * 60)
    print("STARTING AI POLLING SYSTEM")
    print("=" * 60)
    print("\nThe application will start shortly...")
    print("\nAccess the application at:")
    print("  → http://localhost:5000")
    print("  → http://127.0.0.1:5000")
    print("\nDefault Admin Credentials:")
    print("  Email: admin@polls.com")
    print("  Password: Admin@123")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60 + "\n")

    try:
        # Import and run the app
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError:
        print("\n❌ Error: Could not import app.py")
        print("Please make sure app.py is in the current directory")
        return False
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
        return True
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        return False


def main():
    """Main function to run all checks and start the application"""
    print("\n" + "=" * 60)
    print("AI POLLING SYSTEM - STARTUP SCRIPT")
    print("=" * 60 + "\n")

    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("Template Files", check_templates),
        ("Database", check_database)
    ]

    for check_name, check_func in checks:
        if not check_func():
            print(f"\n❌ {check_name} check failed!")
            print("\nPlease fix the issues above and try again.")
            return 1

    print("\n" + "=" * 60)
    print("✓ ALL CHECKS PASSED!")
    print("=" * 60)

    # Start the application
    start_application()
    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n✓ Startup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)