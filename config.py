import os


# Используем относительные пути (папки в корне проекта)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "images")
LOG_DIR = os.path.join(BASE_DIR, "logs")
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}
PAGE_SIZE = 10


# Создаём папки, если их нет
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)