
import sqlite3

def migrate():
    try:
        conn = sqlite3.connect('assettrack.db')
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'avatar_url' not in columns:
            print("Adding avatar_url column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN avatar_url VARCHAR")
            conn.commit()
            print("Migration successful.")
        else:
            print("avatar_url column already exists.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate()
