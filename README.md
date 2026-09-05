# Scraper

Минимальный старт проекта на FastAPI

## Что есть сейчас

- Python 3.12
- FastAPI-приложение с endpoint `GET /health`
- конфигурация через переменные окружения
- асинхронный SQLAlchemy 2.0 и Alembic
- модели `Category`, `Book`, `ScrapeRun`
- Dockerfile
- Docker Compose со связкой `app + PostgreSQL`

## Структура

```text
app/
  config.py
  db/
  main.py
alembic/
alembic.ini
Dockerfile
docker-compose.yml
pyproject.toml
```

## Локальный запуск

1. Создать файл окружения:

```bash
cp .env.example .env
```

2. Создать виртуальное окружение и установить зависимости:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .
```

3. Запустить приложение:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Применить миграции:

```bash
alembic upgrade head
```

5. Проверить health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

## Запуск в Docker

1. Подготовить переменные окружения:

```bash
cp .env.example .env
```

2. Поднять сервисы:

```bash
docker compose up --build
```

3. Применить миграции:

```bash
docker compose exec app alembic upgrade head
```

4. Проверить приложение:

```bash
curl http://127.0.0.1:8000/health
```

## Остановка контейнеров

```bash
docker compose down
```
