#!/bin/bash
set -e

# Wait for database to be ready (if using external database)
if [[ "$DATABASE_URL" == *"postgres"* ]] || [[ "$DATABASE_URL" == *"mysql"* ]]; then
    echo "Waiting for database to be ready..."
    until python -c "import asyncio; from app.db.session import engine; import asyncpg; async def test(): await engine.connect(); await engine.dispose(); asyncio.run(test())" 2>/dev/null; do
        echo "Database is unavailable - sleeping"
        sleep 2
    done
    echo "Database is ready!"
fi

# Initialize database tables
echo "Initializing database tables..."
python -c "
import asyncio
from app.db.session import engine
from app.db.base import Base

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print('Database tables created successfully!')

asyncio.run(init_db())
"

# Seed database if requested
if [[ "$SEED_DATABASE" == "true" ]]; then
    echo "Seeding database with sample data..."
    # Use the installed package to run seed.py
    python -c "
import asyncio
import sys
import os

# Add current directory to Python path to ensure seed.py can import app modules
sys.path.insert(0, '/app')

# Import and run seeding
from seed import main as seed_main

async def run_seed():
    await seed_main()

asyncio.run(run_seed())
"
fi

# Start the application
echo "Starting FastAPI application..."
exec "$@"
