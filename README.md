# Email Assistant

## Идея проекта

### Проблема
- Отсутствие денег и опыта для продвижения продукта

### Целевая аудитория
- Начинающие предприниматели
- Технические специалисты
- Стартапы
- Маркетологи

### MVP (Минимально жизнеспособный продукт)
1. Базовый функционал:
   - Авторизация через Gmail
   - Создание тредов (цепочек писем)
   - Создание персонализированных ИИ-ассистентов
   - Автоматическая генерация и отправка первого сообщения
   - Обработка входящих ответов
   - Генерация ответов от ИИ
   - Автономный режим ответов

### Пользовательский опыт
1. Авторизация в системе
2. Создание личности ассистента
3. Запуск автоматизированного общения
4. Автономная работа системы

## Архитектура

### 1. Основные компоненты

#### Frontend
- Авторизация
- Главная страница
- Боковая панель навигации:
  - Логотип
  - Email assistant
  - Выход
- Интерфейс email assistant:
  - Управление профилями ассистентов
  - Управление тредами
  - История переписки

#### Backend
- SSO авторизация
- Интеграция с Gmail API:
  - Запрос необходимых разрешений
  - Управление учетными данными
- API endpoints:
  - Управление тредами
  - Управление ассистентами
  - Обработка входящей почты
  - Валидация данных и токенов
- Шифрование пользовательских данных

#### Database
- Пользовательские данные
- Треды
- Профили ассистентов
- Gmail credentials

#### Внешние API
- Gmail SDK:
  - Авторизация
  - PubSub API
  - Отправка сообщений
  
### 2. Технологический стек
- Backend: FastAPI
- Frontend: Remix.run
- Database: PostgreSQL
- AI: OpenAI API
- Email: Gmail API
- Messaging: PubSub API

### 3. Архитектурный подход
Монолитная архитектура с разделением на слои:
- Множество оркестраторов по бизнес-процессам

### 4. Структура проектаI
	- alembic
	- core
		- settings.py
		- dependency_injection.py
		- logger.py
		- exception_handler.py
	- config
        - base.py
		- development.py
		- production.py
		- test.py
	- app
		- presentation
			- endpoints
			- schemas
		- aplications
			- orcestrators
			- services
		- infrastructure
			- repositories 
			- integrations
		- domain
			- models
			- exceptions
	- .env.example
    - README.md
    - .env
	- Dokcerfile
	- docker-compose.yml
	- pdm.lock
	- pyproject.toml


**Пошаговая инструкция для создания базового шаблона проекта**

----
1. pdm init
2. pdm add fastapi uvicorn 'pydantic[dotenv]' alembic pydantic-settings==2.4.0
3. pdm add --dev black isort flake8 mypy pytest pytest-asyncio
	1. License(SPDX name) (MIT): **Proprietary**
4. alembic init alembic
5. Создай файл `alembic/env.py` и обнови его так, чтобы он использовал настройки вашего приложения:
6. alembic revision --autogenerate -m "Initial migration"
7. alembic upgrade head

```
mkdir -p alembic core config app/{presentation,applications,infrastructure,domain}
mkdir -p app/presentation/{endpoints,schemas}
mkdir -p app/applications/{orcestrators,services}
mkdir -p app/infrastructure/{repositories,integrations}
mkdir -p app/domain/{models,exceptions}
touch alembic
touch core/{settings.py,dependency_injection.py,logger.py,exception_handler.py}
touch config/{base.py,development.py,production.py,test.py}
touch app/presentation/endpoints/__init__.py
touch app/presentation/schemas/__init__.py
touch app/applications/orcestrators/__init__.py
touch app/applications/services/__init__.py
touch app/infrastructure/repositories/__init__.py
touch app/infrastructure/integrations/__init__.py
touch app/domain/models/__init__.py
touch app/domain/exceptions/__init__.py
touch .env.example
touch Dockerfile
touch docker-compose.yml
