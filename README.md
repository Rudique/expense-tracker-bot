# Expense Tracker Bot

Семейный бот для учёта расходов с напоминаниями, статистикой и мониторингом.

## Требования

- Docker + Docker Compose
- Python 3.12+ (только для локальной разработки)

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Регистрация пользователя |
| `/add_transaction` | Добавить трату |
| `/my_stats` | Личная статистика по периодам |
| `/group_stats` | Общая статистика всех пользователей |
| `/categories` | Список категорий |
| `/add_category` | Добавить категорию |
| `/add_reminder` | Создать напоминание |
| `/my_reminders` | Управление напоминаниями |
| `/set_reminders_topic` | Привязать топик группы для напоминаний (запускать внутри топика) |

## Деплой на сервер

### Первый раз

```bash
git clone https://github.com/Rudique/expense-tracker-bot.git
cd expense-tracker-bot

cp .env.example .env
nano .env  # вписать BOT_TOKEN и TIMEZONE
```

Перелить данные из существующей БД (если есть дамп):

```bash
docker compose up db -d
# подождать 5 секунд
docker exec -i expense-tracker-bot-db-1 psql -U bot expense_bot < dump.sql
docker compose up -d
```

Или запустить с нуля (без данных):

```bash
docker compose up -d
```

### Обновление

```bash
git pull
docker compose up --build -d
```

### CI/CD (GitHub Actions)

При каждом пуше в ветку `main` GitHub автоматически деплоит на сервер.

Необходимые секреты в GitHub → Settings → Secrets:

| Secret | Значение |
|--------|----------|
| `SERVER_HOST` | IP сервера (Tailscale) |
| `SERVER_USER` | Пользователь SSH |
| `SERVER_KEY` | Приватный SSH ключ (`~/.ssh/id_ed25519`) |
| `TAILSCALE_AUTHKEY` | Auth key из Tailscale Admin |

## Переменные окружения

| Переменная | Описание | Пример |
|------------|----------|--------|
| `BOT_TOKEN` | Токен от @BotFather | `123456:ABC...` |
| `DB_URL` | Строка подключения к БД | `postgresql+asyncpg://bot:secret@db:5432/expense_bot` |
| `TIMEZONE` | Часовой пояс для напоминаний | `Asia/Tbilisi` |
| `LOG_LEVEL` | Уровень логов | `INFO` |
| `LOG_FORMAT` | Формат логов (`json` / `pretty`) | `json` |

## Мониторинг

После запуска доступны:

- **Grafana** — `http://localhost:3000` (через SSH туннель: `ssh -L 3000:localhost:3000 user@server`)
- **Loki** — агрегация логов, запросы через Grafana → Explore

Примеры LogQL запросов:

```
# Все логи бота
{job="docker"}

# Только ошибки
{job="docker"} | json | level="error"

# Конкретное событие
{job="docker"} | json | event="transaction_created"

# Все действия пользователя
{job="docker"} | json | user_id="123456"
```

## Локальная разработка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Запустить только БД
docker compose up db -d

# Применить миграции
alembic upgrade head

# Запустить бота
python -m app.main
```

### Миграция данных SQLite → PostgreSQL

```bash
# Запустить БД
docker compose up db -d

# Применить миграции
alembic upgrade head

# Перелить данные
python scripts/migrate_to_pg.py
```
