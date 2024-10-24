# Email Assistant

## Структура базы данных

### Таблица `User` (Пользователь)
- **id** (Primary Key): Уникальный идентификатор пользователя.
- **email**: Email пользователя, используемый для авторизации.
- **is_subscription_active** (Boolean): Флаг, указывающий, активна ли подписка.

### Таблица `Contact` (Контакт)
- **id** (Primary Key): Уникальный идентификатор контакта.
- **user_id** (Foreign Key): Ссылка на `id` пользователя, которому принадлежит контакт.
- **email**: Email контакта.
- **name**: Имя контакта.
- **description**: Описание AI-ассистента.
- **is_active** (Boolean): Флаг, указывающий, активно ли общение с этим контактом (может быть "stop"/"active").
- **deleted_at** (Datetime, Nullable): Дата и время, когда контакт был удален. Это поле позволяет сохранять истоию переписки, но не показывать контакт в активных, если он был удален.

### Таблица `MessageHistory` (История сообщений)
- **id** (Primary Key): Уникальный идентификатор сообщения.
- **user_id** (Foreign Key): Ссылка на пользователя, которому принадлежит переписка.
- **contact_id** (Foreign Key): Ссылка на контакт, с которым ведется переписка.
- **message_direction** (Enum: "sent", "received"): Направление сообщения (отправлено пользователем или получено от контакта).
- **message_text**: Текст сообщения.
- **timestamp**: Временная метка сообщения (дата и время отправки/получения).

### Таблица `ActiveConversation` (Активное общение)
- **id** (Primary Key): Уникальный идентификатор записи.
- **user_id** (Foreign Key): Ссылка на пользователя, который ведет общение.
- **contact_id** (Foreign Key): Ссылка на контакт, с которым ведется общение.
- **last_interaction_at**: Временная метка последнего взаимодействия. Это помогает отслеживать активные разговоры и актуализировать общение.

## Структура проекта
<!-- ``` -->
my_project/
│
├── app/
│   └── core/
│   │   └── config.py
│   ├── main.py
│   ├── endpoints/
│   │   ├── __init__.py
│   │   ├── user_endpoints.py
│   │   └── contact_endpoints.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   └── contact_service.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   └── contact_repository.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── contact.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user_schema.py
│   │   └── contact_schema.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── auth.py
│   └── config.py
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── __init__.py
│   ├── test_users.py
│   └── test_contacts.py
│
└── pdm.lock
<!-- ``` -->


### Описание структуры проекта

- **app/main.py**: Инициализация приложения FastAPI.
- **app/endpoints/**: Содержит маршруты API для различных функциональностей.
  - **user_endpoints.py**: Маршруты, связанные с пользователями.
  - **contact_endpoints.py**: Маршруты, связанные с контактами.
- **app/services/**: Содержит бизнес-логику приложения.
  - **user_service.py**: Логика, связанная с пользователями.
  - **contact_service.py**: Логика, связанная с контактами.
- **app/repositories/**: Содержит операции с базой данных.
  - **user_repository.py**: Операции с данными пользователей.
  - **contact_repository.py**: Операции с данными контактов.
- **app/models/**: Содержит модели базы данных.
  - **user.py**: Модель пользователя.
  - **contact.py**: Модель контакта.
- **app/schemas/**: Содержит Pydantic схемы для валидации данных.
  - **user_schema.py**: Схемы для пользователей.
  - **contact_schema.py**: Схемы для контактов.
- **app/utils/**: Содержит вспомогательные функции.
  - **auth.py**: Функции для аутентификации.
- **app/core/config.py**: Управление настройками приложения.
- **alembic/**: Содержит файлы для миграций базы данных.
- **tests/**: Содержит тесты для приложения.
  - **test_users.py**: Тесты для пользователей.
  - **test_contacts.py**: Тесты для контактов.

Эта структура проекта организована в соответствии с принципами трехслойной архитектуры, что обеспечивает четкое разделение ответственности и упрощает поддержку и развитие приложения.

## Запуск базы данных с помощью Docker

Для запуска локальной базы данных PostgreSQL используйте следующую команду:

### Описание команды

- **docker-compose**: Утилита для управления многоконтейнерными Docker приложениями.
- **up**: Запускает контейнеры, определенные в `docker-compose.yml`.
- **-d**: Запускает контейнеры в фоновом режиме (detached mode).

Эта команда поднимает все сервисы, описанные в `docker-compose.yml`, в том числе и базу данных PostgreSQL, обеспечивая их работу в фоновом режиме. Это позволяет вашему приложению подключаться к базе данных для выполнения операций.

## Команды миграции базы данных

### `alembic revision --autogenerate -m "Create user table"`
Создает файл миграции на основе обнаруженных изменений в моделях SQLAlchemy. Эта команда анализирует разницу между текущей структурой базы данных и определенными моделями, генерируя необходимый Python-код для синхронизации схемы базы данных.

### `alembic upgrade head`
Применяет все неприменённые миграции к базе данных до последней версии. Команда выполняет все необходимые изменения схемы, описанные в файлах миграции, обновляя структуру базы данных до актуального состояния.

```
\l              -- список всех баз данных
\dt             -- список всех таблиц в текущей базе данных
\d имя_таблицы  -- описание структуры конкретной таблицы
\du             -- список пользователей
\conninfo       -- информация о текущем подключении
\q              -- выход из psql
SELECT version();           -- версия PostgreSQL
SELECT current_date;        -- текущая дата
\h                         -- помощь по SQL командам
\?                         -- помощь по командам psql
SELECT * FROM alembic_version; -- инофрмация о миграциях
```

```shell
docker exec -it postgres_db psql -U postgres
```