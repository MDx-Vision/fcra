#!/usr/bin/env python3
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.environ.get('DATABASE_URL', '')

if not DATABASE_URL:
    print("❌ No DATABASE_URL found in environment")
    exit(1)

# Add SSL if needed
if 'sslmode' not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL + "?sslmode=require"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        # Check current column type
        result = conn.execute(text("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'analyses' 
            AND column_name = 'full_analysis'
        """))
        
        row = result.fetchone()
        if row:
            print(f"📊 Current schema:")
            print(f"   Column: {row[0]}")
            print(f"   Type: {row[1]}")
            print(f"   Max Length: {row[2]}")
            
            if row[1] != 'text':
                print(f"\n🔧 Fixing column type from {row[1]} to TEXT...")
                conn.execute(text("ALTER TABLE analyses ALTER COLUMN full_analysis TYPE TEXT"))
                conn.commit()
                print(f"✅ Changed full_analysis to TEXT (unlimited)")
            else:
                print(f"✅ Column is already TEXT type - no change needed")
        else:
            print(f"❌ Column full_analysis not found!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    engine.dispose()
