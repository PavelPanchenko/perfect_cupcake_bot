# Telegram Recipe Bot

Бот для sharing рецептов с медиа контентом.

## Требования

- Docker и Docker Compose
- Poetry (для локальной разработки)

## Установка и запуск

1. Создайте файл `.env`:

```bash
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=[your_admin_telegram_id]
VALID_CODE=you_secret_code
WELCOME_VIDEO_NOTES=[you_video_notes_list]
```

2. Запустите бот через Docker Compose:

```bash
docker-compose up -d
```

### Локальная разработка

1. Установите Poetry:

```bash
pip install poetry
```

2. Установите зависимости:

```bash
poetry install
```

3. Запустите бот:

```bash
poetry run python bot.py
```

## Команды

- /start - Начать работу с ботом
- /recipe - Получить случайный рецепт
- /all_recipes - Получить все доступные рецепты
- /broadcast - Отправить рассылку (только для админа)
- /stats - Статистика пользователей (только для админа)

## Структура проекта

- `bot/` - Основной код бота
    - `__init__.py` - Инициализация модуля
    - `config.py` - Конфигурация и переменные окружения
    - `database.py` - Работа с базой данных
    - `handlers.py` - Обработчики команд
- `data/` - Директория для базы данных (создается автоматически)
- `docker-compose.yml` - Конфигурация Docker Compose
- `Dockerfile` - Инструкции сборки Docker образа
- `pyproject.toml` - Конфигурация Poetry и зависимости