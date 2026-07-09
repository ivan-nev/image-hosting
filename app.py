import os
import uuid
import logging
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, flash, abort, jsonify, send_from_directory
import psycopg2
from werkzeug.utils import secure_filename
from PIL import Image
from db import init_db, save_metadata, get_all_images, delete_image_by_filename, generate_unique_filename

# ------------------ Конфигурация ------------------
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

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# Настройка логирования
log_file = os.path.join(LOG_DIR, "app.log")
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)



# ------------------ Маршруты ------------------
@app.route("/")
def index():
    # Отдаем статический index.html как есть
    return send_from_directory('static', 'index.html')


@app.route("/form/<path:filename>")
def serve_form(filename):
    # Отдаем файлы из папки form (upload.html и т.д.)
    return send_from_directory('static/form', filename)


@app.route("/image-uploader/<path:filename>")
def serve_assets(filename):
    # Отдаем все ассеты (css, js, img)
    return send_from_directory('static/image-uploader', filename)


# API для загрузки файлов (используется upload.js)
@app.route("/api/upload", methods=["POST"])
def api_upload():
    app.logger.info(f"Получен запрос на загрузку, файлов: {len(request.files)}")
    if "file" not in request.files:
        app.logger.warning("Файл не передан в запросе")
        return jsonify({"error": "Файл не выбран"}), 400

    file = request.files["file"]
    app.logger.info(f"Имя файла: {file.filename}, Content-Type: {file.content_type}")

    # Проверка расширения
    original_name = file.filename
    app.logger.info(f"Имя файла: {original_name}, Content-Type: {file.content_type}")

    # Проверяем расширение по исходному имени (без secure_filename)
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        app.logger.warning(f"Неподдерживаемый формат: {ext}")
        return jsonify({"error": f"Неподдерживаемый формат файла: {original_name}"}), 400

    # Проверка размера
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    app.logger.info(f"Размер файла: {size} байт")
    if size > MAX_FILE_SIZE:
        app.logger.warning(f"Превышен размер: {size}")
        return jsonify({"error": f"Файл слишком велик ({size} байт, максимум 5 МБ)"}), 400

    # Проверка через Pillow
    try:
        app.logger.info("Начинаем проверку Pillow")
        img = Image.open(file.stream)
        img_format = img.format.lower()
        app.logger.info(f"Pillow определил формат: {img_format}")
        if img_format not in ["jpeg", "png", "gif"]:
            raise ValueError("Неизвестный формат изображения")
    except Exception as e:
        app.logger.error(f"Ошибка валидации изображения: {str(e)}")
        return jsonify({"error": f"Файл не является корректным изображением: {str(e)}"}), 400

    # ... остальной код

    # Генерация уникального имени и сохранение
    unique_name = generate_unique_filename(original_name)
    save_path = os.path.join(UPLOAD_DIR, unique_name)
    file.seek(0)
    file.save(save_path)

    # Сохранение метаданных
    file_type = img_format if img_format in ["jpg", "png", "gif"] else "jpg"
    try:
        save_metadata(unique_name, original_name, size, file_type)
        logging.info(f"Успех: изображение {unique_name} загружено (ориг. {original_name})")
        # Возвращаем данные в формате, который ожидает upload.js
        return jsonify({
            "success": True,
            "filename": unique_name,
            "original_name": original_name,
            "url": f"/images/{unique_name}"
        }), 200
    except Exception as e:
        os.remove(save_path)
        logging.error(f"Ошибка сохранения метаданных: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500


# API для получения списка файлов (используется images.js)
@app.route("/api/images", methods=["GET"])
def api_images():
    images = get_all_images()
    return jsonify(images), 200


# API для удаления файла (используется images.js)
@app.route("/api/delete/<filename>", methods=["DELETE"])
def api_delete(filename):
    success = delete_image_by_filename(filename)
    if success:
        logging.info(f"Удалено изображение {filename}")
        return jsonify({"success": True}), 200
    else:
        return jsonify({"error": "Файл не найден"}), 404

@app.route("/images/<filename>")
def serve_image(filename):
    safe_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(safe_path):
        abort(404)
    return send_from_directory(UPLOAD_DIR, filename)


# ------------------ Запуск ------------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000, debug=False)