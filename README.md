# Image Hosting — хостинг изображений на Flask + PostgreSQL + Docker

Веб-приложение для загрузки, хранения, просмотра и удаления изображений.  
Поддерживает генерацию миниатюр, пагинацию, автоматическое резервное копирование базы данных.

---

## 🚀 Возможности

- Загрузка изображений (JPEG, PNG, GIF) с проверкой формата и размера
- Автоматическая генерация уникальных имён файлов
- Просмотр галереи с пагинацией
- Генерация миниатюр (thumbnail) с параметрами ширины/высоты
- Удаление изображений
- Асинхронный WSGI‑сервер Gunicorn
- База данных PostgreSQL для хранения метаданных (оригинальное имя, размер, тип, дата загрузки)
- Автоматический бекап базы данных (ежедневно, хранение 7 дней, сжатие gzip)
- Раздача статики через Nginx (или прокси на Flask)
- Полная контейнеризация через Docker Compose

---

## 🧰 Технологии

- **Backend**: Flask + Gunicorn
- **База данных**: PostgreSQL 15
- **Прокси/веб-сервер**: Nginx (или Traefik — см. альтернативный файл)
- **Контейнеризация**: Docker, Docker Compose
- **Работа с изображениями**: Pillow
- **Резервное копирование**: pg_dump, автоматическая ротация

---

## 📁 Структура проекта

```
image-hosting/
├── app.py                 # Основное Flask-приложение
├── config.py              # Конфигурация (пути, лимиты и т.д.)
├── db.py                  # Модуль работы с БД (инициализация, CRUD)
├── db/
│   └── utils.py           # Вспомогательные функции для БД
├── static/                # Статические файлы (HTML, CSS, JS)
│   ├── index.html
│   ├── form/
│   │   └── images.html    # Галерея
│   └── image-uploader/    # Ассеты для загрузчика
├── requirements.txt       # Зависимости Python
├── Dockerfile             # Сборка образа приложения
├── docker-compose.yml     # Основной compose с Nginx + backup
├── docker-compose_traefik.yml  # Альтернатива с Traefik (SSL)
├── nginx.conf             # Конфигурация Nginx
├── backup.sh              # Скрипт резервного копирования БД
├── .env                   # Переменные окружения (не в репозитории)
└── README.md
```

---

## ⚙️ Переменные окружения (файл `.env`)

Создайте `.env` в корне проекта со следующим содержанием (подставьте свои значения):

```ini
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=images_db

# Для приложения
DB_NAME=images_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=db_image           # Имя сервиса в docker-compose
DB_PORT=5432
SECRET_KEY=your-secret-key
DOMAIN=example.com   # Для Traefik (если используется)
```

---

## 🐳 Запуск через Docker Compose

1. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/ivan-nev/image-hosting.git
   cd image-hosting
   ```

2. **Создайте файл `.env`** (см. выше).

3. **Соберите и запустите контейнеры**:
   ```bash
   docker-compose up -d
   ```

   Будут подняты сервисы:
   - `db` – PostgreSQL (порт 5430 на хосте)
   - `app` – Flask + Gunicorn (порт 8000 на хосте)
   - `nginx` – обратный прокси (порт 80 на хосте)
   - `backup` – автоматический бекап БД (каждые 24 часа)

4. **Проверьте работу**:
   - Откройте браузер: http://localhost
   - Загружайте изображения, смотрите галерею.

---

## 📦 Тома (volumes)

- `db_data` – данные PostgreSQL
- `images_data` – загруженные изображения
- `logs_data` – логи приложения
- `backup_data` – дампы базы данных (сжатые .sql.gz)

---

## 🗃️ Работа с бекапами

Бекапы создаются автоматически раз в сутки (можно изменить интервал в `docker-compose.yml`, параметр `sleep` в `command`).  
Дампы хранятся в томе `backup_data` и автоматически удаляются после 7 дней.

**Вручную создать бекап**:
```bash
docker exec backup_image sh /script/backup.sh
```

**Посмотреть список бекапов**:
```bash
docker run --rm -v backup_data:/backups alpine ls -lh /backups
```

**Восстановить из бекапа** (пример):
```bash
docker exec -i db_image psql -U postgres -d images_db < latest_backup.sql
```

---

## 🖼️ API эндпоинты (используются фронтендом)

| Метод | Путь | Описание |
|-------|------|----------|
| POST  | `/api/upload` | Загрузка изображения (multipart/form-data, поле `file`) |
| GET   | `/api/images?page=N` | Получить список изображений (пагинация) |
| DELETE| `/api/delete/<filename>` | Удалить изображение |
| GET   | `/images/<filename>` | Отдать оригинальное изображение |
| GET   | `/thumbnail/<filename>?w=50&h=50` | Отдать миниатюру |

---

## 🔧 Настройка под продакшен

- Вместо `app.run()` используется Gunicorn (уже настроен в `docker-compose.yml`).
- Для HTTPS рекомендуется использовать Traefik (см. `docker-compose_traefik.yml`) или настроить SSL на Nginx.
- Для высоких нагрузок увеличьте количество воркеров Gunicorn в команде запуска.

---

## 🧪 Разработка и отладка

Запуск без Docker (локально):
```bash
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
python app.py
```
(потребуется локальный PostgreSQL и переменные окружения)

---

## 📄 Лицензия

Проект распространяется под лицензией MIT. Используйте свободно.

---

## 👨‍💻 Автор

Иван Невакшёнов / GitHub: https://github.com/ivan-nev/

---

