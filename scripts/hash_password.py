"""Utility script to generate bcrypt password hashes for users.yaml.

Usage:
    python scripts/hash_password.py                  # interactive prompt
    python scripts/hash_password.py "your-password"  # from argument
"""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main():
    import sys

    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        import getpass
        password = getpass.getpass("Enter password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("ERROR: Passwords do not match!")
            sys.exit(1)

    hashed = pwd_context.hash(password)
    print(f"\nGenerated bcrypt hash:\n{hashed}")
    print("\nPaste this into config/users.yaml as password_hash value.")


if __name__ == "__main__":
    main()
