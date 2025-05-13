# API чата

Проект представляет собой API для чат-приложения с поддержкой приватных и групповых чатов.

Стек: FastAPI • PostgreSQL • SQLAlchemy • WebSockets • JWT • Docker • Docker Compose • Pydantic • Python-jose • Passlib • Alembic • Uvicorn • Python 3.x • Swagger/ReDoc

## Запуск проекта

1. Клонируйте репозиторий:
```bash
git clone https://github.com/shumafb/WS-messenger.git
cd WS-messanger
```

2. Запустите проект через Docker Compose:
```bash
docker-compose up -d --build
```

3. После запуска проекта выполните команду для создания тестовых пользователей и чатов:

```bash
docker exec app python -m app.scripts.create_test_data
```

## Создание тестовых данных

Будут созданы следующие тестовые данные:
- 4 пользователя (Алиса, Боб, Чарли, Дэвид)
- Приватный чат между Алисой и Бобом
- Групповой чат "Команда проекта" со всеми пользователями
- Тестовые сообщения в обоих чатах

Данные для входа тестовых пользователей:
- alice@example.com / password123
- bob@example.com / password123
- charlie@example.com / password123
- david@example.com / password123

Приложение будет доступно по адресу: http://localhost:8000

## Основные компоненты проекта:

### JWT Аутентификация:
- Создание токенов
- Верификация токенов
- Управление текущим пользователем

### API Endpoints для аутентификации
- Регистрация (/register)
- Логин (/login)
- Получение информации о пользователе (/me)

### API Endpoints для чатов
- Создание чатов
- Получение списка чатов
- Работа с сообщениями в чатах

### WebSocket соединения
- Поддержка реального времени
- Аутентификация через WebSocket

### База данных
- SQLAlchemy ORM
- Модели пользователей
- Модели чатов и сообщений

### Dependency Injection
- Внедрение зависимостей через FastAPI
- Управление сессиями БД

### Хэширование паролей
- Безопасное хранение
- Верификация паролей

## API Endpoints

### Аутентификация

#### Регистрация
```http
POST /register
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "secretpassword",
    "name": "User Name"
}
```

#### Вход
```http
POST /login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "secretpassword"
}
```

#### Получение информации о текущем пользователе
```http
GET /me
Authorization: Bearer {token}
```

### Чаты

#### Получение списка чатов
```http
GET /chats
Authorization: Bearer {token}
```

#### Создание чата (приватного или группового)
```http
POST /chats
Content-Type: application/json
Authorization: Bearer {token}

{
    "name": "Название чата",
    "chat_type": "private", // или "group"
    "member_ids": [1] // ID пользователя для приватного чата или массив ID для группового
}
```

#### Отправка сообщения
```http
POST /chats/{chat_id}/messages
Content-Type: application/json
Authorization: Bearer {token}

{
    "text": "Текст сообщения"
}
```

#### Получение истории сообщений
```http
GET /chats/{chat_id}/messages
Authorization: Bearer {token}
```

#### Получение истории сообщений с пагинацией
```http
GET /history/{chat_id}?limit=50&offset=0
Authorization: Bearer {token}
```

## WebSocket

Для real-time обмена сообщениями используется WebSocket подключение:

```
ws://localhost:8000/ws/{chat_id}?token={token}
```

### Формат WebSocket сообщений

#### Отправка сообщения
```json
{
    "type": "message",
    "text": "Текст сообщения"
}
```

#### Отметка о прочтении
```json
{
    "type": "read",
    "message_id": 1
}
```

## Документация API

После запуска проекта документация API доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc