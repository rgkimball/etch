#!/usr/bin/env python3
import getpass
from auth import update_admin_credentials

def main():
    print("Set Admin Password")
    print("-----------------")

    while True:
        password = getpass.getpass("Enter new password: ")
        confirm = getpass.getpass("Confirm password: ")

        if password != confirm:
            print("Passwords don't match. Please try again.")
            continue

        if len(password) < 8:
            print("Password must be at least 12 characters long. Please try again.")
            continue

        try:
            update_admin_credentials(password)
            print("Password updated successfully!")
            break
        except Exception as e:
            print(f"Error updating password: {e}")
            break

if __name__ == "__main__":
    main()