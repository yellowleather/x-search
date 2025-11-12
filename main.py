#!/usr/bin/env python3
"""
X-Search Setup & Start Script
Automated setup for local deployment
"""

import argparse
import os
import sys
import subprocess
import shutil
from pathlib import Path


# Colors for terminal output
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color


def print_colored(message, color):
    """Print colored message to terminal"""
    print(f"{color}{message}{Colors.NC}")


def print_header():
    """Print setup header"""
    print("=" * 40)
    print("X-Search - Setup & Start")
    print("=" * 40)
    print()


def check_command(command):
    """Check if a command exists in PATH"""
    return shutil.which(command) is not None


def run_command(cmd, check=True, capture_output=False, shell=False):
    """Run a shell command"""
    try:
        if capture_output:
            result = subprocess.run(
                cmd if shell else cmd.split(),
                capture_output=True,
                text=True,
                check=check,
                shell=shell
            )
            return result
        else:
            subprocess.run(
                cmd if shell else cmd.split(),
                check=check,
                shell=shell
            )
            return None
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return None


def check_and_install_uv():
    """Check if uv is installed, install if not"""
    if not check_command('uv'):
        print_colored("⚠ uv not found - installing...", Colors.YELLOW)
        try:
            # Install uv
            subprocess.run(
                "curl -LsSf https://astral.sh/uv/install.sh | sh",
                shell=True,
                check=True
            )
            # Add to PATH for this session
            cargo_bin = os.path.expanduser("~/.cargo/bin")
            os.environ["PATH"] = f"{cargo_bin}:{os.environ['PATH']}"

            # Verify installation
            if not check_command('uv'):
                print_colored("Error: Failed to install uv", Colors.RED)
                print("Please install manually: https://github.com/astral-sh/uv")
                sys.exit(1)
        except subprocess.CalledProcessError:
            print_colored("Error: Failed to install uv", Colors.RED)
            print("Please install manually: https://github.com/astral-sh/uv")
            sys.exit(1)

    print_colored("✓ uv found", Colors.GREEN)


def check_python():
    """Check if Python 3 is available"""
    if not check_command('python3'):
        print_colored("Error: Python 3 not found", Colors.RED)
        sys.exit(1)

    print_colored("✓ Python found", Colors.GREEN)


def check_postgresql():
    """Check if PostgreSQL is installed"""
    if not check_command('psql'):
        print_colored("⚠ PostgreSQL not found", Colors.YELLOW)
        print()
        print("Please install PostgreSQL:")
        print("  macOS: brew install postgresql@14")
        print("  Linux: sudo apt-get install postgresql")
        print()
        sys.exit(1)

    print_colored("✓ PostgreSQL found", Colors.GREEN)


def setup_database(db_name: str, db_user: str):
    """Auto-create database and user if they don't exist"""
    print("Setting up database...")

    # Check if database exists
    result = run_command(
        "psql -d postgres -lqt",
        check=False,
        capture_output=True,
        shell=True
    )

    if result and result.returncode == 0:
        databases = result.stdout
        if db_name not in databases:
            print(f"Creating database '{db_name}'...")
            run_command(f"createdb -h localhost {db_name}", check=False, shell=True)

    # Check if user exists
    result = run_command(
        f"psql -d postgres -tc \"SELECT 1 FROM pg_user WHERE usename = '{db_user}'\"",
        check=False,
        capture_output=True,
        shell=True
    )

    if result and result.returncode == 0:
        if '1' not in result.stdout:
            print(f"Creating user '{db_user}'...")
            run_command(f"createuser -h localhost -s {db_user}", check=False, shell=True)

    print_colored("✓ Database setup complete", Colors.GREEN)


def setup_env_file():
    """Check and create .env file if needed"""
    if not os.path.exists('.env'):
        print_colored("⚠ .env file not found", Colors.YELLOW)
        print()
        print("Creating .env from example...")
        shutil.copy('.env.example', '.env')
        print_colored("✓ Created .env", Colors.GREEN)
        print()
        print("Please edit .env and add your ANTHROPIC_API_KEY")
        print("Then run this script again")
        sys.exit(0)

    print_colored("✓ .env file exists", Colors.GREEN)


def setup_venv():
    """Create virtual environment with uv"""
    if not os.path.exists('.venv'):
        print("Creating virtual environment with uv...")
        run_command("uv venv", shell=True)
        print_colored("✓ Virtual environment created", Colors.GREEN)


def activate_venv():
    """Activate virtual environment by modifying PATH and environment"""
    venv_bin = os.path.join(os.getcwd(), '.venv', 'bin')
    os.environ["PATH"] = f"{venv_bin}:{os.environ['PATH']}"
    os.environ["VIRTUAL_ENV"] = os.path.join(os.getcwd(), '.venv')


def install_dependencies():
    """Install dependencies with uv"""
    print("Installing dependencies with uv (this is fast!)...")
    run_command("uv pip install -e .", shell=True)
    print_colored("✓ Dependencies installed", Colors.GREEN)


def check_database_connection(db_name: str, db_user: str):
    """Test database connection"""
    print("Checking database connection...")

    # We need to run this with the venv python
    venv_python = os.path.join('.venv', 'bin', 'python')
    result = run_command(
        f'{venv_python} -c "from src.database.connection import db; exit(0 if db.test_connection() else 1)"',
        check=False,
        capture_output=True,
        shell=True
    )

    if result and result.returncode == 0:
        print_colored("✓ Database connected", Colors.GREEN)
    else:
        print_colored("⚠ Database connection failed", Colors.YELLOW)
        print()
        if result and result.stderr:
            print("Error details:")
            print(result.stderr)
            print()
        print("Make sure PostgreSQL is running and database exists:")
        print(f"  createdb {db_name}")
        print(f"  createuser -s {db_user}")
        print()
        sys.exit(1)


def init_database():
    """Apply schema SQL to ensure database is ready"""
    print("Running database migrations...")
    venv_python = os.path.join('.venv', 'bin', 'python')
    run_command(f"{venv_python} src/database/migrate.py", shell=True)
    print_colored("✓ Migrations complete", Colors.GREEN)


def import_tweets_if_needed():
    """Import tweets if data file exists and database is empty"""
    data_file = Path("inputs/twitter/data/like.js")

    if not data_file.exists():
        print_colored("⚠ No Twitter data found", Colors.YELLOW)
        print()
        print("Place your Twitter data export file at:")
        print("  inputs/twitter/data/like.js")
        print()
        print("Then run: python src/ingestion/import_likes.py")
        print()
        return

    print_colored("✓ Twitter data file found", Colors.GREEN)

    # Check if we need to import
    venv_python = os.path.join('.venv', 'bin', 'python')
    result = run_command(
        f"{venv_python} -c \"from src.database.connection import db; r = db.execute_query('SELECT COUNT(*) as count FROM tweets'); print(r[0]['count'] if r else 0)\"",
        check=False,
        capture_output=True,
        shell=True
    )

    tweet_count = 0
    if result and result.returncode == 0:
        try:
            tweet_count = int(result.stdout.strip())
        except ValueError:
            tweet_count = 0

    if tweet_count == 0:
        print("No tweets in database. Importing...")
        run_command(f"{venv_python} src/ingestion/import_likes.py", shell=True)
        print_colored("✓ Tweets imported", Colors.GREEN)
    else:
        print_colored(f"✓ Found {tweet_count} tweets in database", Colors.GREEN)


def generate_embeddings_if_needed():
    """Generate embeddings if they don't exist"""
    embeddings_dir = Path("data/vector_store/tweets")

    if not embeddings_dir.exists():
        print("Generating embeddings (this may take a while)...")
        venv_python = os.path.join('.venv', 'bin', 'python')
        run_command(f"{venv_python} src/processing/batch_processor.py --task embeddings", shell=True)
        print_colored("✓ Embeddings generated", Colors.GREEN)
    else:
        print_colored("✓ Embeddings already exist", Colors.GREEN)


def start_streamlit():
    """Start Streamlit UI"""
    print()
    print("=" * 40)
    print_colored("Setup Complete!", Colors.GREEN)
    print("=" * 40)
    print()
    print("Starting Streamlit UI...")
    print("Access at: http://localhost:8501")
    print()

    venv_python = os.path.join('.venv', 'bin', 'python')
    streamlit = os.path.join('.venv', 'bin', 'streamlit')

    # Use streamlit directly if available, otherwise use python -m
    if os.path.exists(streamlit):
        subprocess.run([streamlit, "run", "src/ui/app.py"])
    else:
        subprocess.run([venv_python, "-m", "streamlit", "run", "src/ui/app.py"])


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="X-Search setup helper")
    parser.add_argument(
        "--db-name",
        default="xsearch",
        help="Name of the PostgreSQL database to create/use (default: xsearch)"
    )
    parser.add_argument(
        "--db-user",
        default="xsearch_user",
        help="PostgreSQL superuser to create/use for the app (default: xsearch_user)"
    )
    return parser.parse_args()


def main(db_name: str, db_user: str):
    """Main setup and start workflow"""
    print_header()

    # Prerequisites
    check_and_install_uv()
    check_python()
    check_postgresql()

    # Database setup
    setup_database(db_name, db_user)

    # Environment setup
    setup_env_file()

    # Python environment
    setup_venv()
    activate_venv()
    install_dependencies()

    # Database initialization
    check_database_connection(db_name, db_user)
    init_database()

    # Data import and processing
    import_tweets_if_needed()
    generate_embeddings_if_needed()

    # Start the application
    start_streamlit()


if __name__ == "__main__":
    args = parse_args()
    try:
        main(args.db_name, args.db_user)
    except KeyboardInterrupt:
        print()
        print_colored("Setup interrupted by user", Colors.YELLOW)
        sys.exit(0)
    except Exception as e:
        print()
        print_colored(f"Error: {e}", Colors.RED)
        sys.exit(1)
