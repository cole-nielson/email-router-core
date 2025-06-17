#!/usr/bin/env python3
"""
Admin User Creation Script for Email Router
🔐 Creates initial super admin user for system bootstrapping.

Usage:
    python scripts/create_admin_user.py --username admin --email admin@example.com --password securepass123
    python scripts/create_admin_user.py --interactive
"""

import argparse
import getpass
import os
import sys
from pathlib import Path

# Add the app directory to the path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.connection import init_database
from app.database.models import User, UserRole, UserStatus
from app.services.auth_service import AuthService


def validate_password(password: str) -> bool:
    """Validate password strength."""
    if len(password) < 8:
        print("❌ Password must be at least 8 characters long")
        return False

    if not any(c.isupper() for c in password):
        print("❌ Password must contain at least one uppercase letter")
        return False

    if not any(c.islower() for c in password):
        print("❌ Password must contain at least one lowercase letter")
        return False

    if not any(c.isdigit() for c in password):
        print("❌ Password must contain at least one number")
        return False

    return True


def validate_email(email: str) -> bool:
    """Basic email validation."""
    return "@" in email and "." in email.split("@")[-1]


def create_admin_user(username: str, email: str, password: str, full_name: str = None) -> bool:
    """
    Create a super admin user.

    Args:
        username: Username for the admin
        email: Email address for the admin
        password: Password for the admin
        full_name: Full name (optional)

    Returns:
        True if user was created successfully, False otherwise
    """
    try:
        # Initialize database
        print("🔧 Initializing database...")
        init_database()

        # Import SessionLocal after initialization
        from app.database.connection import SessionLocal

        # Create database session
        db = SessionLocal()
        auth_service = AuthService(db)

        # Check if user already exists
        existing_user = (
            db.query(User).filter((User.username == username) | (User.email == email)).first()
        )

        if existing_user:
            print(f"❌ User with username '{username}' or email '{email}' already exists")
            if existing_user.username == username:
                print(f"   Existing username: {existing_user.username}")
            if existing_user.email == email:
                print(f"   Existing email: {existing_user.email}")
            return False

        # Validate inputs
        if not validate_email(email):
            print(f"❌ Invalid email format: {email}")
            return False

        if not validate_password(password):
            return False

        # Create user
        print(f"👤 Creating super admin user: {username}")

        hashed_password = auth_service.hash_password(password)

        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            full_name=full_name or f"Super Admin ({username})",
            role=UserRole.SUPER_ADMIN,
            client_id=None,  # Super admin is not tied to a specific client
            status=UserStatus.ACTIVE,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"✅ Super admin user created successfully!")
        print(f"   ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Full Name: {user.full_name}")
        print(f"   Role: {user.role.value}")
        print(f"   Status: {user.status.value}")
        print(f"   Created: {user.created_at}")

        return True

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False
    finally:
        if "db" in locals():
            db.close()


def interactive_mode():
    """Interactive mode for creating admin user."""
    print("🔐 Email Router - Admin User Creation")
    print("=" * 40)

    # Get username
    while True:
        username = input("Username: ").strip()
        if username:
            break
        print("❌ Username cannot be empty")

    # Get email
    while True:
        email = input("Email: ").strip()
        if email and validate_email(email):
            break
        print("❌ Please enter a valid email address")

    # Get full name (optional)
    full_name = input("Full Name (optional): ").strip()
    if not full_name:
        full_name = f"Super Admin ({username})"

    # Get password
    while True:
        password = getpass.getpass("Password: ")
        if validate_password(password):
            break

    # Confirm password
    while True:
        confirm_password = getpass.getpass("Confirm Password: ")
        if password == confirm_password:
            break
        print("❌ Passwords do not match")

    # Confirm creation
    print(f"\n📋 Summary:")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Full Name: {full_name}")
    print(f"   Role: super_admin")

    confirm = input("\nCreate this admin user? (y/N): ").strip().lower()
    if confirm in ["y", "yes"]:
        return create_admin_user(username, email, password, full_name)
    else:
        print("❌ User creation cancelled")
        return False


def list_existing_admins():
    """List existing admin users."""
    try:
        init_database()
        from app.database.connection import SessionLocal

        db = SessionLocal()

        admin_users = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).all()

        if not admin_users:
            print("📭 No super admin users found")
            return

        print("👥 Existing Super Admin Users:")
        print("-" * 40)
        for user in admin_users:
            status_icon = "✅" if user.status == UserStatus.ACTIVE else "❌"
            print(f"{status_icon} {user.username} ({user.email})")
            print(f"   ID: {user.id}")
            print(f"   Full Name: {user.full_name}")
            print(f"   Status: {user.status.value}")
            print(f"   Created: {user.created_at}")
            if user.last_login_at:
                print(f"   Last Login: {user.last_login_at}")
            print()

    except Exception as e:
        print(f"❌ Error listing admin users: {e}")
    finally:
        if "db" in locals():
            db.close()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Create super admin user for Email Router",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (recommended)
  python scripts/create_admin_user.py --interactive

  # Command line mode
  python scripts/create_admin_user.py --username admin --email admin@company.com --password SecurePass123

  # List existing admin users
  python scripts/create_admin_user.py --list

  # Create with full name
  python scripts/create_admin_user.py --username johndoe --email john@company.com --password SecurePass123 --full-name "John Doe"
        """,
    )

    # Add mutually exclusive group for different modes
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive mode (recommended)"
    )
    mode_group.add_argument(
        "--list", "-l", action="store_true", help="List existing super admin users"
    )
    mode_group.add_argument("--username", "-u", help="Username for the admin user")

    # Arguments for command line mode
    parser.add_argument("--email", "-e", help="Email address for the admin user")
    parser.add_argument(
        "--password", "-p", help="Password for the admin user (not recommended for security)"
    )
    parser.add_argument("--full-name", "-n", help="Full name for the admin user")

    args = parser.parse_args()

    # Handle different modes
    if args.interactive:
        success = interactive_mode()
        sys.exit(0 if success else 1)

    elif args.list:
        list_existing_admins()
        sys.exit(0)

    elif args.username:
        # Command line mode
        if not args.email:
            print("❌ Email is required when using --username")
            parser.print_help()
            sys.exit(1)

        if not args.password:
            # Prompt for password if not provided
            args.password = getpass.getpass(f"Password for {args.username}: ")

        success = create_admin_user(args.username, args.email, args.password, args.full_name)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
