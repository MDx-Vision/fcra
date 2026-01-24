#!/usr/bin/env python3
"""
Database seed script for Cypress E2E testing.
Clears all existing data and creates a single test user.
"""

import os
import sys

os.environ.setdefault('DATABASE_URL', os.getenv('DATABASE_URL', ''))

from werkzeug.security import generate_password_hash
from database import SessionLocal, Base, engine, Staff

def clear_all_data():
    """Clear all data from the database."""
    session = SessionLocal()
    try:
        meta = Base.metadata
        with engine.begin() as conn:
            for table in reversed(meta.sorted_tables):
                print(f"Clearing table: {table.name}")
                conn.execute(table.delete())
        print("All tables cleared successfully.")
    except Exception as e:
        print(f"Error clearing data: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def create_test_user():
    """Create a single test user for E2E testing."""
    session = SessionLocal()
    try:
        test_user = Staff(
            email='test@example.com',
            password_hash=generate_password_hash('password123'),
            first_name='Test',
            last_name='User',
            role='admin',
            is_active=True
        )
        session.add(test_user)
        session.commit()
        print(f"Test user created: {test_user.email}")
        return test_user
    except Exception as e:
        print(f"Error creating test user: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def seed_database():
    """Main seed function."""
    print("=" * 50)
    print("DATABASE SEED SCRIPT")
    print("=" * 50)
    print()
    
    print("Step 1: Clearing all existing data...")
    clear_all_data()
    print()
    
    print("Step 2: Creating test user...")
    user = create_test_user()
    print()
    
    print("=" * 50)
    print("SEED COMPLETE")
    print("=" * 50)
    print(f"Test User Email: test@example.com")
    print(f"Test User Password: password123")
    print("=" * 50)

if __name__ == '__main__':
    seed_database()
