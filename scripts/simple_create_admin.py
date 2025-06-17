#!/usr/bin/env python3
"""
Simple Admin User Creation Script for Email Router
🔐 Creates initial super admin user without complex relationships.
"""

import getpass
import sys
from pathlib import Path

# Add the app directory to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def create_simple_admin():
    """Create admin user with minimal database interaction."""
    try:
        # Load environment variables first
        from dotenv import load_dotenv

        load_dotenv()

        from app.database.connection import init_database

        print("🔧 Initializing database...")
        init_database()

        from app.database.connection import SessionLocal
        from app.services.auth_service import AuthService

        # Get user input
        print("\n🔐 Create Super Admin User")
        print("=" * 30)

        username = input("Username: ").strip()
        if not username:
            print("❌ Username cannot be empty")
            return False

        email = input("Email: ").strip()
        if not email or "@" not in email:
            print("❌ Please enter a valid email")
            return False

        password = getpass.getpass("Password: ")
        if len(password) < 8:
            print("❌ Password must be at least 8 characters")
            return False

        full_name = input("Full Name (optional): ").strip()
        if not full_name:
            full_name = f"Super Admin ({username})"

        # Create user using raw SQL to avoid relationship issues
        db = SessionLocal()
        auth_service = AuthService(db)

        # Check if user exists using raw query
        from sqlalchemy import text

        result = db.execute(
            text("SELECT id FROM users WHERE username = :username OR email = :email"),
            {"username": username, "email": email},
        ).fetchone()

        if result:
            print(f"❌ User with username '{username}' or email '{email}' already exists")
            return False

        # Hash password
        hashed_password = auth_service.hash_password(password)

        # Insert user using raw SQL
        db.execute(
            text(
                """
            INSERT INTO users (
                username, email, password_hash, full_name, role, status,
                login_attempts, jwt_token_version, api_access_enabled,
                rate_limit_tier, created_at, updated_at
            ) VALUES (:username, :email, :password_hash, :full_name, :role, :status,
                     0, 1, 1, 'standard', datetime('now'), datetime('now'))
        """
            ),
            {
                "username": username,
                "email": email,
                "password_hash": hashed_password,
                "full_name": full_name,
                "role": "super_admin",
                "status": "active",
            },
        )

        db.commit()

        # Get the created user ID
        result = db.execute(
            text("SELECT id, created_at FROM users WHERE username = :username"),
            {"username": username},
        ).fetchone()

        user_id, created_at = result

        print(f"\n✅ Super admin user created successfully!")
        print(f"   ID: {user_id}")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Full Name: {full_name}")
        print(f"   Role: super_admin")
        print(f"   Status: active")
        print(f"   Created: {created_at}")

        print(f"\n🔑 You can now log in with:")
        print(f"   Username: {username}")
        print(f"   Password: [hidden]")

        return True

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        if "db" in locals():
            db.close()


def list_admins():
    """List existing admin users."""
    try:
        from dotenv import load_dotenv

        load_dotenv()

        from app.database.connection import init_database

        init_database()
        from app.database.connection import SessionLocal

        db = SessionLocal()

        from sqlalchemy import text

        results = db.execute(
            text(
                """
            SELECT id, username, email, full_name, status, created_at, last_login_at
            FROM users
            WHERE role = 'super_admin'
            ORDER BY created_at
        """
            )
        ).fetchall()

        if not results:
            print("📭 No super admin users found")
            return

        print("👥 Existing Super Admin Users:")
        print("-" * 50)
        for row in results:
            user_id, username, email, full_name, status, created_at, last_login = row
            status_icon = "✅" if status == "active" else "❌"
            print(f"{status_icon} {username} ({email})")
            print(f"   ID: {user_id}")
            print(f"   Full Name: {full_name}")
            print(f"   Status: {status}")
            print(f"   Created: {created_at}")
            if last_login:
                print(f"   Last Login: {last_login}")
            print()

    except Exception as e:
        print(f"❌ Error listing admin users: {e}")
    finally:
        if "db" in locals():
            db.close()


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_admins()
    else:
        create_simple_admin()


if __name__ == "__main__":
    main()
