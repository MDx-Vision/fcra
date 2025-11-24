import os
from sqlalchemy import create_engine, text
import re

# Get DATABASE_URL and clean it
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Remove problematic connection parameters
# Replit adds these but psycopg2 doesn't understand them
DATABASE_URL = re.sub(r'[?&]statement_timeout=\d+', '', DATABASE_URL)
DATABASE_URL = re.sub(r'[?&]sslmode=[^&]*', '', DATABASE_URL)

print(f"Using cleaned DATABASE_URL")

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check current type
        print("📊 Checking current column type...")
        result = conn.execute(text("""
            SELECT data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'analyses' AND column_name = 'full_analysis'
        """))
        
        row = result.fetchone()
        if row:
            print(f"   Current type: {row[0]}")
            print(f"   Max length: {row[1] if row[1] else 'unlimited'}")
            
            if row[0] != 'text':
                print("\n🔧 Changing column to TEXT...")
                conn.execute(text("ALTER TABLE analyses ALTER COLUMN full_analysis TYPE TEXT"))
                conn.commit()
                print("✅ Changed to TEXT")
                
                # Verify
                result = conn.execute(text("""
                    SELECT data_type, character_maximum_length 
                    FROM information_schema.columns 
                    WHERE table_name = 'analyses' AND column_name = 'full_analysis'
                """))
                row = result.fetchone()
                print(f"\n✅ Verified new type: {row[0]}, Max length: {row[1] if row[1] else 'unlimited'}")
            else:
                print("✅ Column is already TEXT type!")
        else:
            print("❌ Column 'full_analysis' not found in 'analyses' table")
            
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTry running this in Replit Shell instead:")
    print("  Nix> psql $DATABASE_URL")
    print("  psql> ALTER TABLE analyses ALTER COLUMN full_analysis TYPE TEXT;")
    print("  psql> \\q")
