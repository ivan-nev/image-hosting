import os
import logging
from logging.handlers import RotatingFileHandler
from io import BytesIO
from flask import Flask, request, abort, jsonify, send_from_directory, send_file
from PIL import Image, ImageOps
from db import (init_db, save_metadata, get_all_images, delete_image_by_filename, generate_unique_filename,
                get_images_page, get_total_images_count, get_total_images)
from config import LOG_DIR, UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE, PAGE_SIZE

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# Настройка логирования
log_file = os.path.join(LOG_DIR, "app.log")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")

# Ротация по размеру
file_handler = RotatingFileHandler(
    log_file, maxBytes=1*1024*1024, backupCount=5, encoding='utf-8'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)



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
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1
    items = get_images_page(page)
    total = get_total_images()
    return jsonify({
        "items": items,
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE
    }), 200


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


@app.route("/thumbnail/<filename>")
def thumbnail(filename):
    # Проверяем, существует ли файл
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        abort(404)

    # Параметры размера (по умолчанию 50x50)
    try:
        width = request.args.get('w', 50, type=int)
        height = request.args.get('h', 50, type=int)
    except ValueError:
        width = height = 50

    # Открываем изображение
    img = Image.open(filepath)

    # Сохраняем пропорции и обрезаем до квадрата (центрированно)
    # Если хотите просто ресайз с сохранением пропорций без обрезки, используйте thumbnail
    # но для списка лучше квадратная миниатюра
    img.thumbnail((width, height), Image.LANCZOS)

    # Если нужно строго квадратное изображение, можно сделать обрезку:
    # from PIL import ImageOps
    # img = ImageOps.fit(img, (width, height), Image.LANCZOS, centering=(0.5, 0.5))))

    # Определяем формат
    fmt = img.format if img.format else 'JPEG'
    # Сохраняем в байтовый поток
    output = BytesIO()
    img.save(output, format=fmt, quality=85)
    output.seek(0)

    # Отправляем с правильным типом
    return send_file(output, mimetype=f'image/{fmt.lower()}',
                     max_age=3600)


# ------------------ Запуск ------------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000, debug=False)