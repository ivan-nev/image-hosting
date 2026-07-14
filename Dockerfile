FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаём точки монтирования
RUN mkdir -p /images /logs

EXPOSE 8000

CMD ["python", "app.py"]