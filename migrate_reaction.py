"""
Database Migration Script for Guest Reactions
Run this script to update your existing database with the new email field for reactions
"""

import sqlite3
import os


def migrate_database():
    """Migrate the database to support guest reactions"""

    db_path = 'polling_system.db'

    if not os.path.exists(db_path):
        print("❌ Database not found!")
        print("Please run 'python app.py' first to create the database.")
        return False

    print("\n" + "=" * 60)
    print("DATABASE MIGRATION - Adding Guest Reaction Support")
    print("=" * 60 + "\n")

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("✓ Connected to database")

        # Check if email column already exists in reactions table
        cursor.execute("PRAGMA table_info(reactions)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'email' in columns:
            print("✓ Email column already exists in reactions table")
        else:
            print("Adding email column to reactions table...")
            cursor.execute("ALTER TABLE reactions ADD COLUMN email VARCHAR(120)")
            print("✓ Email column added successfully")

        # Make user_id nullable (if it isn't already)
        # SQLite doesn't support ALTER COLUMN, so we need to check the current schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='reactions'")
        schema = cursor.fetchone()[0]

        if 'user_id INTEGER NOT NULL' in schema:
            print("\nUpdating reactions table to make user_id nullable...")

            # Create new table with correct schema
            cursor.execute("""
                CREATE TABLE reactions_new (
                    id INTEGER PRIMARY KEY,
                    poll_id INTEGER NOT NULL,
                    user_id INTEGER,
                    email VARCHAR(120),
                    reaction_type VARCHAR(20) NOT NULL,
                    timestamp DATETIME,
                    FOREIGN KEY (poll_id) REFERENCES polls(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Copy data from old table
            cursor.execute("""
                INSERT INTO reactions_new (id, poll_id, user_id, email, reaction_type, timestamp)
                SELECT id, poll_id, user_id, email, reaction_type, timestamp
                FROM reactions
            """)

            # Drop old table
            cursor.execute("DROP TABLE reactions")

            # Rename new table
            cursor.execute("ALTER TABLE reactions_new RENAME TO reactions")

            print("✓ Reactions table updated successfully")
        else:
            print("✓ User_id column is already nullable")

        # Commit changes
        conn.commit()
        conn.close()

        print("\n" + "=" * 60)
        print("✓ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nGuest users can now react to polls by providing their email.")
        print("No data was lost during migration.\n")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nYou may need to recreate the database. To do this:")
        print("1. Backup your current database: copy polling_system.db polling_system_backup.db")
        print("2. Delete the database: rm polling_system.db (or del polling_system.db on Windows)")
        print("3. Run: python app.py")
        print("4. Run: python init_db.py --with-samples\n")
        return False


def check_migration_needed():
    """Check if migration is needed"""

    db_path = 'polling_system.db'

    if not os.path.exists(db_path):
        print("Database not found. No migration needed.")
        print("Run 'python app.py' to create a new database.")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if email column exists
        cursor.execute("PRAGMA table_info(reactions)")
        columns = [column[1] for column in cursor.fetchall()]

        conn.close()

        if 'email' not in columns:
            return True
        else:
            print("✓ Database is already up to date!")
            return False

    except Exception as e:
        print(f"Error checking database: {e}")
        return False


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("GUEST REACTION MIGRATION CHECKER")
    print("=" * 60 + "\n")

    if check_migration_needed():
        print("Migration is required.\n")
        response = input("Do you want to proceed with migration? (y/n): ")

        if response.lower() == 'y':
            success = migrate_database()
            if success:
                print("\n✓ You can now restart your application!")
                print("  python app.py\n")
        else:
            print("\nMigration cancelled.")
    else:
        print("\nNo migration needed!")

    print("=" * 60 + "\n")