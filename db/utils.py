import os
import uuid
import psycopg2
import logging
from config import UPLOAD_DIR, ALLOWED_EXTENSIONS, PAGE_SIZE


# ------------------ Подключение к БД ------------------
def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ.get("DB_NAME", "images_db"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "password"),
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5430")
    )


# Инициализация таблицы
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            size INTEGER NOT NULL,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_type TEXT NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    logging.info("База данных и таблица images созданы / проверены")


# ------------------ Вспомогательные функции ------------------
def allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def generate_unique_filename(original_name):
    ext = os.path.splitext(original_name)[1]
    return f"{uuid.uuid4().hex}{ext}"


def save_metadata(filename, original_name, size, file_type):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO images (filename, original_name, size, file_type) VALUES (%s, %s, %s, %s)",
        (filename, original_name, size, file_type)
    )
    conn.commit()
    cur.close()
    conn.close()


def get_all_images():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, filename, original_name, size, upload_time, file_type FROM images ORDER BY upload_time DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "filename": row[1],
            "original_name": row[2],
            "size": row[3],
            "upload_time": row[4].strftime("%Y-%m-%d %H:%M:%S"),
            "file_type": row[5]
        })
    return result


def delete_image_by_filename(filename):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM images WHERE filename = %s", (filename,))
    deleted = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    if deleted:
        filepath = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    return deleted



def get_total_images_count():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM images")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

# Вместо get_all_images используем get_images_page
def get_images_page(page):
    offset = (page - 1) * PAGE_SIZE
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, filename, original_name, size, upload_time, file_type "
        "FROM images ORDER BY upload_time DESC LIMIT %s OFFSET %s",
        (PAGE_SIZE, offset)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "filename": row[1],
            "original_name": row[2],
            "size": row[3],
            "upload_time": row[4].strftime("%Y-%m-%d %H:%M:%S"),
            "file_type": row[5]
        })
    return result

def get_total_images():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM images")
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return total
