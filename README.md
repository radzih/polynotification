# PolyNotification Bot

A scalable Telegram bot template built with Python, `aiogram`, and Clean Architecture principles.

## 🏗 Architecture

This project follows the **Clean Architecture** (Onion Architecture) pattern to ensure separation of concerns, scalability, and testability.

The project structure is organized as follows:

```
src/
├── bootstrap/      # Application startup, configuration, and factories
├── domain/         # Business entities and protocols (interfaces)
├── infrastructure/ # External tools (DB, APIs) and implementations of protocols
│   └── db/
│       ├── alembic/      # Database migrations
│       ├── models/       # SQLAlchemy ORM models
│       └── repositories/ # Repository implementations
├── presentation/   # Interface layer (Handlers, Middlewares, Dialogs)
└── use_cases/      # Application business logic (Interactors)
```

### Key Technologies

- **Framework**: `aiogram 3.x` (Async Telegram Bot API)
- **Database**: `SQLAlchemy 2.0` (Async ORM), `aiosqlite` (SQLite driver)
- **Migrations**: `Alembic`
- **Configuration**: `pydantic-settings`
- **Dependency Injection**: Custom Middlewares

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Git
- Redis 7+ (local instance or via `docker-compose`)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd polynotification
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. **Environment Variables**
   Copy the example environment file and configure your bot token:
   ```bash
   cp env.example .env
   ```
   Edit `.env` and set your `BOT_TOKEN` obtained from @BotFather. You can also override `DATABASE_URL` or any of the `REDIS_*` values if you're not using the defaults (host `localhost`, port `6379`, DB `0`, optional password).

2. **Database Setup**
   Apply the database migrations to create the SQLite database and tables:
   ```bash
   alembic upgrade head
   ```

### Running the Bot

Run the application as a module:

```bash
python -m src.main
```

### Redis State Storage

FSM and dialog states are persisted in Redis. If you use the provided `docker-compose.yml`, a Redis service is already defined and the bot container is configured to talk to it. For local development without Docker, ensure a Redis instance is running and reachable via the connection parameters defined in `.env`.

## 🛠 Development

### Creating Migrations

After modifying SQLAlchemy models (`src/infrastructure/db/models/`), generate a new migration:

```bash
alembic revision --autogenerate -m "description of changes"
```

Then apply it:

```bash
alembic upgrade head
```

### Adding a New Feature

1. **Domain**: Define entities and protocols (interfaces) in `src/domain/`.
2. **Infrastructure**: Implement protocols (e.g., repositories) in `src/infrastructure/`.
3. **Use Case**: Implement business logic in `src/use_cases/`.
4. **Presentation**: Create handlers in `src/presentation/` and register them in `src/main.py`.

