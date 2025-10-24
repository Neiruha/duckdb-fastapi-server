Архитектура и состав

Ядро: FastAPI + Uvicorn, Python 3.12.

Слои:

server/routers/* — HTTP-роуты (вьюхи).

server/services/* — предметная логика/агрегации.

server/db/* — доступ к БД (репозитории, sandbox).

server/middleware/access.py — аутентификация/авторизация.

server/config.py — конфигурация (env → константы).

server/schemas/* — Pydantic-схемы запросов/ответов.

server/logging_utils.py — ротация логов в /srv/neiruha/lab/app/server/logs/*.log.

БД: DuckDB (прод) с возможной Postgres-абстракцией. Схема — db/schema/schema.sql.
Миграции — db/updates/YYYY-MM-DD_<slug>.sql + дублирующий YYYY-MM-DD_<slug>.py (сам коннектится к DuckDB через DUCKDB_PATH).

Деплой: systemd-unit ashva-fastapi.service (Uvicorn на 127.0.0.1:8010; nginx — reverse proxy, TLS/HTTP/2).

Журналы и аудит: таблица sys_events, типы событий — справочник sys_event_types.

Конфигурация (env)

Основные переменные окружения:

DUCKDB_PATH — путь к боевой БД.

DEMO_MODE (true|false) — включает «демо» поведение и стойкие фолбэки.

TOKENS — словарь server-токенов; в исходниках остаётся только phil_token_zxcvbnhjaks.

MINIAPP_BOT_TOKEN — токен телеграм-бота для верификации init_data мини-приложения.

Сглаживание:

SMOOTH_SERIES_INTERVAL = day|week (по умолчанию day)

SMOOTH_SERIES_MAX_POINTS = 366

SMOOTH_WEIGHTS = {teacher:0.5, mentor:0.3, student:0.2}

SMOOTH_GAP_STRATEGY = linear|carry (задумано linear)

Sandbox:

SANDBOX_DB_COPY_PATH — путь к копии /srv/neiruha/lab/app/data/_sandbox.duckdb (по умолчанию там же).

Кеш по mtime оригинала; thread-safe (Lock).

CORS:

Разрешается домен клиента (nginx отдает Access-Control-Allow-Origin под известные фронтенды).

Модель безопасности
Токены и «кто такой вызвавший»

Server-token: строковый секрет из TOKENS.

Всегда проходит require_token() и не ограничивается банами/заморозкой.

Доступ ко всем роутам, включая POST /api/v1/select, любые пользователи/треки.

Client-token: записывается в таблицу client_tokens, вид 'ct_<hex>'.

Выдаётся только если пользователь не frozen и не banned.

В middleware валидируется по БД: существует, не revoked_at, не истёк.

В каждый Depends(require_token) возвращаем:

class Caller:
    kind: Literal["server","client"]
    user_id: str | None
    telegram_user_id: int | None


При любом запросе с client_token:

если user.frozen → 403 {"detail":"ACCOUNT_FROZEN"}

если user.banned → 403 {"detail":"ACCOUNT_BANNED"}
(исключение: при выдаче токена на /sessions/connect/miniapp — там тексты ниже).

Хелперы доступа:

require_token(allow_server=True, allow_client=False) — по умолчанию старое поведение (server-token впускается всегда).

need_client_role() → require_token(allow_server=False, allow_client=True) — когда нужен обязательно клиентский токен.

Роли/права с client_token

Доступ к сглаженным сериям: клиент может запрашивать только:

серию по себе (student_id == caller.user_id), или

если он teacher в треке (track_participants даёт роль учителя).
Иначе 403.

Сообщения my/sent: только свои входящие/исходящие.

Mark-read: только свои входящие (server-token — по любому списку).

Сессии и Mini App
POST /api/v1/sessions/connect/miniapp

Без авторизации. Тело:

{
  "telegram_user_id": 123,
  "telegram_username": "nick",
  "telegram_login_name": "nick",
  "display_name": "Имя",
  "init_data": "<raw initData>",
  "user_agent": "MiniApp/1.0 (...)",
  "ip_hash": "sha256(...)",
  "ttl_minutes": 1440
}


Логика:

Проверить подпись init_data (HMAC-SHA256 c MINIAPP_BOT_TOKEN) по правилам Telegram Mini Apps.

Найти пользователя по telegram_user_id. Если нет — создать (как в обычном /sessions/connect), но frozen=true.

Если user.banned → 404 Not Found (притворяемся отсутствием).
Если user.frozen → 401 Unauthorized, текст: «Ваш аккаунт заморожен администратором.»

Сгенерировать client_token = ct_<24hex>, записать в client_tokens (user_id, tg_id, ip_hash, user_agent, payload_json = parsed init_data, expires_at = now + ttl).

Вернуть:

{
  "client_token": "ct_...",
  "user_id": "u_...",
  "telegram_user_id": 123,
  "expires_at": "2025-..(Europe/Warsaw ISO)"
}


В sys_events: client_token_issued (context: "via sessions/connect/miniapp").

POST /api/v1/sessions/client/revoke

Требуется client-token. Тело пустое. Помечает токен revoked_at=now.
Ответ: {"ok":true}; событие client_token_revoked.

POST /api/v1/sessions/client/refresh

Требуется client-token. Опц. ttl_minutes. Обновляет expires_at.
Если revoked/expired → 401. Событие client_token_refreshed.

(Старые /api/v1/sessions/connect|refresh|disconnect остаются с тем же контрактом; server-token остаётся «суперпользователем».)

Справочники (refdata)

Все требуют require_token() (server или client):

GET /api/v1/metrics → массив {metric_id, name, description?}.

GET /api/v1/metric-types → {id, name, description}.

GET /api/v1/track-step-types → {id, name, description}.

GET /api/v1/sys-event-types → {id, name, description}.

(опц.) GET /api/v1/message-types → {id, name, description}.

Сортировка по name.

Оценки и метрики
«Сырьё» (уже существующие, расширены полями)

GET /api/v1/scores/track/{track_id} (фильтры: student_id?, metric_id?, since?, until?, limit, offset)

GET /api/v1/scores/student/{student_id} (фильтры: track_id?, metric_id?, since?, until?, limit, offset)

POST /api/v1/scores/query — списки track_ids[], student_ids[], metric_ids[], since, until, пагинация.

Ответная запись (расширенная):

{
  "score_id": "...",
  "step_id": "...",
  "track_id": "...",
  "student_id": "...",
  "metric_id": "m_disc_01",
  "metric_name": "Дисциплина",
  "value_raw": 73,
  "value_smooth": 75,
  "rater_user_id": "...",
  "role_at_rate": "teacher|mentor|student",
  "comment": "...",
  "occurred_at": "2025-10-15T10:10:00Z"
}


Правило «точечного» сглаживания: value_smooth = clamp(0..100, value_raw) с лёгкой нормировкой; «настоящее» сглаживание — в сериях.

Сглаженные временные серии (новый роут)

GET /api/v1/scores/smoothed-series
Параметры:

track_id — обязательно

student_id — опционально (агрегат по всем студентам трека, если не задан)

metric_id — опционально (если не задан — «composite» по всем метрикам)

interval — day|week (по умолчанию из конфига)

max_points — ограничитель (по умолчанию из конфига)

since, until — границы (по умолчанию track.start_at/end_at)

Формат ответа:

{
  "interval": "day",
  "points": [
    {
      "t": "2025-10-01",
      "self_weighted": 64.2,
      "teacher_weighted": 71.0,
      "mentor_weighted": 58.9,
      "composite": 66.7
    }
  ]
}


Как считаем:

Разбиваем интервал (day|week).

Собираем оценки student|teacher|mentor по «окнам».

Применяем сглаживание (скользящее среднее/EMA α=0.3 — фиксированно и детерминированно).

Пробелы интерполируем согласно SMOOTH_GAP_STRATEGY (по умолчанию linear).

composite = 0.5*teacher + 0.3*mentor + 0.2*self (веса из SMOOTH_WEIGHTS).

Гарантируем диапазон 0..100.
Ограничения доступа см. раздел «Роли/права».

Пользователи и треки

GET /api/v1/users (limit, offset) → { total, items:[{user_id, display_name, telegram_id?, telegram_username?, web_login?, last_seen_at?}] }

PATCH /api/v1/users/{user_id} — {"display_name": "..."} → переименование (server/client в рамках прав администратора).

POST /api/v1/users/info — resolve-инфо по telegram_user_id|username|user_id → UserInfoOut (активные треки и куратор).

GET /api/v1/tracks/active — активные треки (для панелей/справочника).

GET /api/v1/tracks/teacher/{user_id} — треки, где пользователь — преподаватель (active_only по умолчанию true).

GET /api/v1/tracks/student/{user_id} — треки, где пользователь — студент.

PATCH /api/v1/tracks/{track_id} — {"title":"..."} → переименование.

Профили/флаги/health/dbalive

GET /api/v1/health — liveness (без авторизации).

GET /api/v1/dbalive — краткая статистика БД (требует токен).

GET /api/v1/flags/telegram/{telegram_user_id} — флаги frozen/banned по Telegram.

GET /api/v1/profiles/by-telegram/{telegram_user_id} — объединённый профиль, активные треки, last_seen_at.

Сообщения (inbox/outbox)

Таблицы messages, message_recipients, message_types уже есть.

GET /api/v1/messages/my — входящие текущего клиента.
Параметры: limit (1..200), offset >=0, unread_only?, since?, until?.
Ответ элементы:

{
  "message_id":"msg_...",
  "message_type":"text|...",
  "content":"Привет!",
  "message_data_json":{...},
  "sender_user_id":"u_...",
  "created_at":"...",
  "read_flag": true|false
}


GET /api/v1/messages/sent — исходящие текущего клиента (аналогично).

POST /api/v1/messages/send — отправить:

{
  "to_telegram_user_id": 555777999,
  "message_type": "text",
  "content": "Привет!",
  "data": { "any": "json" }
}


Поиск/разрешение получателя: должен существовать пользователь с этим Telegram ID (в демо — можно любому).
Создаём запись в messages и message_recipients (read_flag=false).
Ответ: { "message_id": "msg_...", "recipient_user_id": "u_..." }.
Событие message_sent (actor=sender, subject=recipient).

POST /api/v1/messages/mark-read — пометить входящие прочитанными:
{"message_ids":["msg_...","msg_..."]} → {"updated": N}.
Клиент может менять только свои входящие; server-token — любые.
Событие message_read.

SELECT-песочница

POST /api/v1/select — только server-token.
Тело: {"sql": "SELECT ...", "params": [ ... ] }
Защиты:

Разрешены только SELECT.../WITH...SELECT.

Запрещены ATTACH, COPY, PRAGMA, EXPORT, ; внутри, SQL-комментарии --.

Работа только на копии БД: ensure_copy_up_to_date() поддерживает read-only коннект к клон-файлу по mtime.
Ответ:

{ "columns": ["col1","col2"], "rows": [[...], [...]] }


Важно: не использовать в обычных флоу. (И ты просил тоже: «не пользоваться SQL-раутом без острой надобности».)

Аудит (sys_events)

Фиксируем:

user_created (как раньше).

client_token_issued|revoked|refreshed (с subject_user_id, context: "via sessions/connect/miniapp"|"client/revoke"|"client/refresh").

message_sent, message_read.
Поля: event_type, actor_user_id?, subject_user_id?, context, created_at.

Ошибки/ответы (правила отказов)

Невалидный/просроченный client_token → 401 Unauthorized.

Client_token при заморозке/бане:

403 {"detail":"ACCOUNT_FROZEN"} / 403 {"detail":"ACCOUNT_BANNED"}.

/sessions/connect/miniapp:

user.banned → 404 Not Found

user.frozen → 401 "Ваш аккаунт заморожен администратором."

Доступ к чужим данным с client_token → 403.

Валидация входных схем — стандартный 422 от FastAPI.

Производительность и лимиты

Пагинация limit/offset на списках (пределы: users ≤ 1000; scores ≤ 2000 — по умолчанию 200).

SMOOTH_SERIES_MAX_POINTS — защита от чересчур длинных рядов.

Индексы в DuckDB на ключевых полях (client_tokens.user_id, telegram_user_id, expires_at и т.п.).

Развёртывание/сервис

WorkingDirectory=/srv/neiruha/lab/app/server

ExecStart=/srv/neiruha/lab/app/.venv/bin/uvicorn server.server:app --host 127.0.0.1 --port 8010 --proxy-headers --forwarded-allow-ips="*" --workers 2 --timeout-keep-alive 75

User=neiruha

Environment:

VIRTUAL_ENV=/srv/neiruha/lab/app/.venv

PATH=/srv/neiruha/lab/app/.venv/bin:...

PYTHONUNBUFFERED=1

PYTHONPATH=/srv/neiruha/lab/app/server:/srv/neiruha/lab/app

DUCKDB_PATH=...

MINIAPP_BOT_TOKEN=...

и др. по списку выше.

Папка логов /srv/neiruha/lab/app/server/logs принадлежит пользователю neiruha, права 750/640.

Nginx: проксирует https://neiruha.space → 127.0.0.1:8010, добавляет нужные CORS заголовки.

Мини-клиент (HTML)

Однофайловый клиент (тот, что мы отладили) использует:

/users → выбрать ученика

/tracks/student/{user} → выбрать трек

/metrics → список метрик (иначе — фолбэк локальным списком)

/scores/smoothed-series (или фолбэк на /scores/student) → построить 12 графиков
Встроенный логгер выводит каждый fetch (с маскировкой токена), ошибки сети/CORS, полезную подсказку.
