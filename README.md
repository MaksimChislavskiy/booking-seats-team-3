# ☕ Cafe Booking API

Backend-сервис для бронирования столов в кафе с поддержкой ролей пользователей, управлением кафе, слотами времени и фоновыми задачами напоминаний.

---

## 🚀 Основной функционал

- 👤 Управление пользователями (регистрация, редактирование, блокировка)
- 🔐 Аутентификация и авторизация (JWT)
- 🏪 Управление кафе, столами и временными слотами
- 📅 Бронирование столов по дате и времени
- ✏️ Изменение и отмена бронирований
- ⏰ Напоминание о бронировании (через Celery)
- 🔔 Уведомление администратора о событиях бронирования

---

## 🛠 Стек технологий

- Python 3.12
- FastAPI
- SQLAlchemy 2.0 (async)
- PostgreSQL
- Redis
- Celery
- Docker, Docker Compose
- Alembic

---

## ▶️ Запуск проекта

### 🔹 Вариант 1. Запуск через Docker (рекомендуется)

```bash
docker compose -f infra/docker-compose.yml up --build
```
## После запуска сервис доступен по адресу:
```bash
http://localhost:8000
```
* Swagger-документация:
```bash
http://localhost:8000/docs
```

### 🔹 Вариант 2. Локальный запуск (без Docker)
* Создать виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate
```

* Установить зависимости:
```bash
pip install -r requirements.txt
```
* Запустить PostgreSQL и Redis локально
- Применить миграции:
```bash
alembic upgrade head
```

* Запустить сервер:
```bash
uvicorn app.main:app --reload
```
*  Автоматическое создание администратора

При старте приложения создаётся администратор, если он отсутствует в БД.
Данные берутся из .env:
```bash
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_EMAIL=root@mail.com
INITIAL_ADMIN_PASSWORD=root1234
```

### 🔔 Фоновые задачи (Celery)
 Celery используется для:
- отправки напоминаний о бронировании
- уведомления администратора о событиях бронирования
-Брокер и backend: Redis
-Запуск воркера происходит в отдельном контейнере celery.
Логи Celery можно смотреть через:
```bash
docker logs cafe-celery
```

### 📚 Основные эндпоинты
- /auth/login
- /users
- /cafes
- /cafe/tables
- /cafe/slots
- /booking

## Полный список доступен в Swagger.
📎 Документация API
Swagger:
```bash
http://localhost:8000/docs
```
OpenAPI файл: openapi.yml

### 👥 Роли пользователей
- ADMIN — полный доступ
- MANAGER — управление своим кафе
- USER — создание и управление своими бронированиями
- Права доступа реализованы на уровне сервисов и эндпоинтов.