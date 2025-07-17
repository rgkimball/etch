from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import secrets
import yaml
from pathlib import Path
import os

ph = PasswordHasher()


def get_project_root() -> Path:
    """Returns project root folder."""
    # Get the directory containing the current file (auth.py)
    current_file = Path(__file__).resolve()
    # Return its parent directory (project root)
    return current_file.parent


def get_config_path() -> Path:
    """Returns the absolute path to config.yaml"""
    return get_project_root() / 'config.yml'


def generate_salt():
    """Generate a cryptographically secure salt"""
    return secrets.token_hex(16)


def hash_password(password: str, salt: str) -> str:
    """Hash a password with a salt using Argon2"""
    return ph.hash(f"{password}{salt}")


def verify_password(password: str, salt: str, hash: str) -> bool:
    """Verify a password against a hash"""
    try:
        return ph.verify(hash, f"{password}{salt}")
    except VerifyMismatchError:
        return False


def update_admin_credentials(password: str):
    """Update admin password in config file"""
    config_path = get_config_path()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    salt = generate_salt()
    password_hash = hash_password(password, salt)

    # Update config
    if 'admin' not in config:
        config['admin'] = {}
    config['admin']['password_hash'] = password_hash
    config['admin']['salt'] = salt

    # Write to temp file first
    temp_path = config_path.with_suffix('.yaml.tmp')
    with open(temp_path, 'w') as f:
        yaml.safe_dump(config, f)

    # Rename temp file to actual file
    os.replace(temp_path, config_path)


def verify_admin_password(password: str) -> bool:
    """Verify admin password against stored hash"""
    config_path = get_config_path()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    if 'admin' not in config:
        return False

    stored_hash = config['admin'].get('password_hash')
    salt = config['admin'].get('salt')

    if not stored_hash or not salt:
        return False

    return verify_password(password, salt, stored_hash)