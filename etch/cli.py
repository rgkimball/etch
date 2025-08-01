import os
import shutil
import sys
from pathlib import Path

EXCLUDE = {"__pycache__", "cli.py", "__init__.py"}
BARE_CONTENT_DIRS = {"pages", "posts", "projects"}

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Create a new Etch site.")
    parser.add_argument("name", help="Project directory name or '.' for current directory")
    parser.add_argument("-b", "--bare", action="store_true", help="Omit sample content (bare scaffold)")
    args = parser.parse_args()

    destination = Path(args.name).resolve()

    if destination.exists() and any(destination.iterdir()) and args.name != ".":
        print(f"Error: Directory '{args.name}' already exists and is not empty.")
        sys.exit(1)

    try:
        source = Path(__file__).parent
    except ImportError as e:
        print(f"Error: Couldn't locate Etch source files. Expected: {source}\n{e}")
        sys.exit(1)

    # If etching into '.', warn if not empty
    if destination.exists() and any(destination.iterdir()) and args.name == ".":
        print("⚠️  Current directory is not empty. Files may be overwritten.")
        confirm = input("Proceed with copying? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            sys.exit(0)
    elif not destination.exists():
        destination.mkdir(parents=True)

    for item in source.iterdir():
        if item.name in EXCLUDE:
            continue

        dest_path = destination / item.name

        # If --bare is set, skip copying contents of these folders
        if args.bare and item.name in BARE_CONTENT_DIRS:
            dest_path.mkdir(parents=True, exist_ok=True)
            continue

        if item.is_dir():
            shutil.copytree(item, dest_path, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest_path)

    print(f"✅ Etch site files copied to: {destination}")
    print("Next steps:\n")
    if args.name != ".":
        print(f"  cd {args.name}")
    print("  flask run  # or python app.py")
