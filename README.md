# Email AI Backend

The Email Assistant platform allows users to organize autonomous communication with mailboxes on their behalf. The system is based on integration with Gmail API and LLM (Large Language Model), which provides automated thread creation, generation of personalized responses, and configuration of unique AI assistant personalities through custom instructions.

---

## Table of Contents

1. [Project Idea](#project-idea)
2. [Architecture](#architecture)
   - [Main Components](#main-components)
   - [External APIs](#external-apis)
3. [Technology Stack](#technology-stack)
4. [Architectural Approach](#architectural-approach)
5. [Project Structure](#project-structure)
6. [Data Models](#data-models)
7. [Key Components](#key-components)
   - [Orchestrators](#orchestrators)
   - [Services](#services)
   - [Factories](#factories)
8. [Data Processing Flow](#data-processing-flow)
9. [Project Setup and Launch](#project-setup-and-launch)
10. [Working with Migrations](#working-with-migrations)

---

## Project Idea

### Problem
- Lack of financial resources and experience for effective product promotion.

### Target Audience
- Beginning entrepreneurs.
- Technical specialists.
- Startups.
- Marketers.

### MVP (Minimum Viable Product)
1. **Basic Functionality:**
   - Authorization through Gmail.
   - Creation of threads (email chains).
   - Creation of personalized AI assistants.
   - Automatic generation and sending of the first message.
   - Processing of incoming responses.
   - Generation of AI responses.
   - Autonomous response mode.

### User Experience
1. Authorization in the system.
2. Creating an assistant personality.
3. Launching automated communication.
4. Autonomous system operation.

---

## Architecture

### Main Components

#### Frontend
- **Authorization:** Login via Gmail.
- **Main Page:** Primary platform interface.
- **Side Navigation Panel:**
  - Logo.
  - Email Assistant.
  - Logout button.
- **Email Assistant Interface:**
  - Management of assistant profiles.
  - Management of threads (email chains).
  - Correspondence history.

#### Backend
- **SSO Authorization:** Processing login via Gmail.
- **Integration with Gmail API:**
  - Requesting necessary permissions.
  - Managing user credentials.
  - Tracking changes in the mailbox (watch).
  - Getting mail history changes.
- **API Endpoints:**
  - Thread management.
  - Assistant management.
  - Incoming mail processing.
  - Data and token validation.
- **Data Encryption:** Ensuring user data security.

#### Database
- Storage of:
  - User data.
  - Threads.
  - Assistant profiles.
  - Gmail credentials.
  - Watch history for Gmail.

#### External APIs

- **Gmail SDK:**
  - Authorization.
  - PubSub API for receiving notifications.
  - Sending messages.
  - Getting history of changes.

- **OpenAI API:**
  - Creating assistants.
  - Creating threads.
  - Generating responses.
  - Managing conversation context.

---

## Technology Stack

- **Backend:** FastAPI.
- **Frontend:** Remix.run.
- **Database:** PostgreSQL with asynchronous access via SQLAlchemy.
- **AI:** OpenAI API (Assistants API).
- **Email:** Gmail API.
- **Messaging:** Google PubSub API.
- **Authentication:** OAuth2 via Authlib.
- **Migrations:** Alembic.
- **Dependency Management:** PDM.

---

## Architectural Approach

The application is implemented using a monolithic architecture with clear layer separation and application of the following patterns:

- **Factory Method:** For creating services and adapters (OpenAIFactory, AuthServiceFactory).
- **Repository:** Abstraction layer for working with the database.
- **Adapter:** For integration with external APIs (GoogleAuthAdapter, OpenAIAdapter).
- **Orchestrator:** For coordinating business processes between different services.
- **Interfaces and DI:** Using interfaces and dependency injection to ensure flexibility and testability.

The project structure follows clean architecture principles with division into:
- **Presentation:** API endpoints and data schemas.
- **Business Logic (applications):** Orchestrators, services, and factories.
- **Infrastructure:** Repositories and integrations with external systems.
- **Domain:** Data models, interfaces, and business exceptions.

---

## Data Models

- **Users:** Information about system users.
- **OAuthCredentials:** OAuth authorization data (tokens, lifetime).
- **GmailAccount:** Information about connected Gmail accounts and their tracking status.
- **AssistantProfiles:** Assistant profiles with instructions and capabilities.
- **EmailThreads:** Email chains with statuses (active/stopped).

---

## Key Components

### Orchestrators
- **AuthOrchestrator:** Manages the authentication process.
- **AssistantOrchestrator:** Creation and management of OpenAI assistants.
- **EmailThreadOrchestrator:** Management of email chains and integration with Gmail and OpenAI.

### Services
- **GoogleAuthenticationService:** Authentication through Google.
- **OpenAIAssistantService:** Working with OpenAI assistants.
- **OpenAIThreadService:** Working with OpenAI threads.
- **GmailService:** Working with Gmail API.
- **EmailThreadService:** Managing email chains in the database.

### Factories
- **OpenAIFactory:** Creating services and adapters for working with OpenAI.
- **AuthServiceFactory:** Creating authentication services.

---

## Data Processing Flow

1. **Authentication:**
   - User authorizes through Google OAuth.
   - The system saves tokens and creates a user account.

2. **Creating an Assistant:**
   - User creates an assistant profile with instructions.
   - The system creates an assistant in OpenAI and saves its ID.

3. **Creating a Thread:**
   - User sets thread parameters (recipient, instructions).
   - The system creates a thread in OpenAI and sets up tracking in Gmail.

4. **Autonomous Operation:**
   - Gmail notifies the system about new emails via PubSub.
   - The system retrieves the email content and passes it to the OpenAI thread.
   - OpenAI generates a response based on context and instructions.
   - The system sends the response via Gmail API.

---

## Project Setup and Launch

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd email-asistent
   ```

2. Environment setup:
   ```bash
   cp .env.example .env
   # Edit .env, adding your API keys and database configuration
   ```

3. Install dependencies using PDM:
   ```bash
   pdm install
   ```

4. Apply migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

## Working with Migrations

1. Create a new migration:
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```

2. Apply migrations:
   ```bash
   alembic upgrade head
   ```

3. Rollback to previous version:
   ```bash
   alembic downgrade -1
   ```

4. Get current version:
   ```bash
   alembic current
   ```

---

## Project Structure

```
├── alembic                     # Database migrations
│   ├── versions                # Migration versions
│   ├── env.py                  # Environment settings for migrations
│   └── script.py.mako          # Template for generating migrations
├── core                        # Application core
│   ├── settings.py             # Application settings
│   ├── dependency_injection.py # Dependency injection
│   ├── logger.py               # Logging configuration
│   └── exception_handler.py    # Exception handlers
├── config                      # Configurations for different environments
│   ├── base.py                 # Base configuration
│   ├── development.py          # Development configuration
│   ├── production.py           # Production configuration
│   └── test.py                 # Test configuration
├── app                         # Main application code
│   ├── presentation            # Presentation layer
│   │   ├── endpoints           # API endpoints
│   │   └── schemas             # Data schemas (Pydantic)
│   ├── applications            # Application layer
│   │   ├── orchestrators       # Business process orchestrators
│   │   ├── services            # Services
│   │   └── factories           # Factories for object creation
│   ├── infrastructure          # Infrastructure layer
│   │   ├── repositories        # Repositories for DB operations
│   │   └── integrations        # Integrations with external services
│   └── domain                  # Domain layer
│       ├── models              # Data models
│       ├── interfaces          # Interfaces
│       └── exceptions          # Domain exceptions
├── .env.example                # Example environment configuration
├── README.md                   # Project documentation
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose configuration
├── pdm.lock                    # PDM dependencies lock file
└── pyproject.toml              # Project configuration and dependencies
```
