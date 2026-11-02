# Коробка с книгами (Book Box)

Telegram-бот, который помогает найти книгу по душе и проверить свои литературные знания в викторине. 
Проект демонстрирует навыки асинхронного программирования, работы с внешними API, проектирования баз данных и реализации игровых механик.

## Основные возможности

* **Рекомендации:** Подбор книг по 10 жанрам с использованием Google Books API. Умная фильтрация (только книги на русском или английском языках) и кэширование для экономии лимитов API.
* **Список «Хочу прочитать»:** Сохранение понравившихся книг в личную библиотеку (просмотр списка с прямыми ссылками на книги).
* **Литературная викторина:** База из 50 вопросов разных типов (цитаты, авторы, содержание). Начисление опыта (XP) за правильные ответы и повышение уровня.
* **Коллекция ачивок:** За достижение новых уровней пользователь получает «котиков» (картинки). Коллекцию можно просматривать в профиле.
* **Профиль и Лидерборд:** Красивая карточка профиля с прогресс-баром опыта, статистикой избранного и топ-10 лучших читателей.
* **Надежность:** Обработка ошибок внешнего API (graceful degradation), защита от SQL-инъекций (ORM), валидация ввода и глобальная обработка исключений.

---

## Технологический стек

* **Язык:** Python 3.11+ (используется 3.12)
* **Telegram Framework:** `aiogram 3.x` (асинхронный)
* **База данных:** `SQLite` (через асинхронный `SQLAlchemy 2.0` + `aiosqlite`)
* **HTTP-клиент:** `httpx` (для запросов к API)
* **Внешние API:** `Google Books API`, `Open Library` (резервный)
* **Отказоустойчивость:** `tenacity` (повторные попытки при сбоях сети)
* **Настройки:** `pydantic-settings` (чтение `.env`)

---

## Инструкция по развертыванию

### 1. Клонирование репозитория
```bash
git clone https://github.com/ТВОЙ_НИК/book-box.git
cd book-box
```

### 2. Установка виртуального окружения и зависимостей
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate

# Установка библиотек
pip install -r requirements.txt
```

### 3. Получение ключей API
1. **Telegram Bot Token:** Найди в Telegram бота `@BotFather`, отправь `/newbot`, придумай имя и username. Скопируй полученный токен.
2. **Google Books API Key:** Зайди в [Google Cloud Console](https://console.cloud.google.com/), создай проект, включи **Books API** и создай ключ в разделе Credentials.

### 4. Настройка `.env`
Создай файл `.env` в корне проекта (на основе `.env.example`) и заполни его:
```env
# Токен бота от BotFather
BOT_TOKEN=1234567890:AAH-xxxxxxxxxxxxxxxxxxxxxxxx

# Ключ Google Books API
GOOGLE_BOOKS_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxx

# Прокси (если требуется для обхода блокировок в вашей стране)
PROXY_URL=http://user:pass@host:port

# URL базы данных (по умолчанию SQLite)
DATABASE_URL=sqlite+aiosqlite:///./book_box.db
```

### 5. Наполнение базы вопросов (Опционально)
Если вы хотите загрузить 50 вопросов для викторины (файл `seeds/quiz_seed.py` уже содержит их):
```bash
python seeds/quiz_seed.py
```

### 6. Запуск бота
```bash
python main.py
```

---

## 🗄 Схема базы данных

Проект использует 5 таблиц, связанных между собой:

```mermaid
erDiagram
    USERS {
        int id PK
        bigint tg_id UK
        string username
        string first_name
        int xp
        int level
        datetime created_at
    }
    WISHLIST_ITEMS {
        int id PK
        int user_id FK
        string title
        string authors
        string thumbnail
        string info_link
        datetime added_at
    }
    QUIZ_QUESTIONS {
        int id PK
        string question_text
        string option_1
        string option_2
        string option_3
        string option_4
        int correct_option
        string category
        int points
    }
    USER_ACHIEVEMENTS {
        int id PK
        int user_id FK
        string achievement_code
        datetime unlocked_at
    }
    API_CACHE {
        string key PK
        json value
        datetime expires_at
    }

    USERS ||--o{ WISHLIST_ITEMS : "имеет"
    USERS ||--o{ USER_ACHIEVEMENTS : "получает"
```

* **users:** Профили пользователей (ID в Telegram, опыт, уровень).
* **wishlist_items:** Список «Хочу прочитать» (связь с `users`).
* **quiz_questions:** Банк вопросов для викторины.
* **user_achievements:** Выданные ачивки (связь с `users`).
* **api_cache:** Кэш ответов от Google Books API (с TTL).

---

## Структура проекта (Чистая архитектура)

```text
book-box/
├── bot/                  # Логика Telegram-бота
│   ├── handlers/         # Обработчики команд и кнопок (user, menu, quiz, profile)
│   ├── keyboards/        # Inline и Reply клавиатуры
│   ├── middlewares/      # Прослойки (DbSessionMiddleware для сессий и user)
│   ├── states/           # FSM (машины состояний) для викторины и рекомендаций
│   └── utils/            # Вспомогательные функции
├── database/             # Настройка движка SQLAlchemy и Base
├── models/               # Модели БД (User, WishlistItem, QuizQuestion, ApiCache, UserAchievement)
├── repositories/         # Слой доступа к данным (CRUD-операции)
├── services/             # Бизнес-логика (работа с Google Books, ачивки)
├── seeds/                # Скрипты наполнения БД (вопросы для викторины)
├── assets/               # Медиа-файлы (картинки котиков для ачивок)
├── config/               # Настройки (pydantic-settings)
├── .env.example          # Шаблон переменных окружения
├── requirements.txt      # Зависимости проекта
└── main.py               # Точка входа (запуск поллинга)
```

---

## Особенности реализации (Что посмотреть на защите)

1. **Кэширование API:** Вместо того чтобы каждый раз дергать Google Books, ответы сохраняются в таблицу `api_cache` с временем жизни 24 часа. Это защищает от лимитов API и ускоряет ответ бота.
2. **Graceful Degradation:** Если Google Books недоступен (упал, таймаут, заблокирован), бот не падает, а сообщает пользователю «Сервис временно недоступен». Используются ретраи (`tenacity`).
3. **Защита от «спагетти-кода»:** Строгое разделение слоев. Хэндлеры не делают запросы к БД напрямую, они вызывают методы репозиториев и сервисов.
4. **Машина состояний (FSM):** Для викторины и рекомендаций используется `FSMContext`, что позволяет корректно обрабатывать нажатия кнопок, даже если пользователь перезапустит бота или нажмет старую кнопку (защита от начисления XP дважды).
5. **Геймификация:** Реализована система уровней (каждые 100 XP повышают уровень) и коллекция достижений. При повышении уровня пользователю приходит картинка котика.
