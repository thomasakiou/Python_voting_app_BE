import os
from typing import Optional
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)


def hash(password: str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def delete_candidate_image_file(image_url: Optional[str]) -> bool:
    """
    Safely deletes a candidate's image file from disk when deleted or replaced.
    Handles URLs like '/candidates/images/<file>', '/uploads/candidates/<file>',
    full URLs, and local relative paths.
    """
    if not image_url or not isinstance(image_url, str):
        return False

    # Extract the file basename cleanly, ignoring query parameters/hashes
    clean_url = image_url.split("?")[0].split("#")[0].strip()
    if not clean_url:
        return False

    filename = os.path.basename(clean_url)
    # Don't delete if it's default placeholder or empty
    if not filename or filename.lower() in ("default.png", "avatar.png", "placeholder.png", "user.png", ""):
        return False

    # Security check: avoid directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        return False

    # Possible directories where candidate images might be stored
    possible_paths = [
        os.path.join("uploads", "candidates", filename),
        os.path.join("uploads", filename),
    ]

    deleted = False
    for path in possible_paths:
        try:
            if os.path.exists(path) and os.path.isfile(path):
                os.remove(path)
                deleted = True
        except Exception as e:
            print(f"Warning: Could not remove candidate image file {path}: {e}")

    return deleted