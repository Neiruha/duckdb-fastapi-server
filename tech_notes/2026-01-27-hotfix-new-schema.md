# HOTFIX отчет: запуск сервера на новой схеме БД (2026-01-27)

## Контекст
База данных уже приведена к `db/schema/new_schema.sql`. Требовалось адаптировать код сервера под актуальную схему без миграций и без создания таблиц в рантайме.

## Что сделано

### 1) Bootcheck (startup safe check)
- Убрано создание таблиц `metric_groups` и `metric_group_members`.
- Убрана статистика/агрегации по группам метрик (она больше не существует в новой схеме).
- Добавлена валидация наличия обязательных таблиц: `users`, `metrics`, `tracks`, `scores`.
- Сохранён ровно один безопасный write-тест: обновление `users.last_connected` для `DB_SERVER_USER`.
- Логика write-теста больше не затрагивает таблицу `sessions`.

### 2) Scores (DB + DTO)
- Удалено сглаживание (smoothing) и clamp-логика в `scores_repo`.
- `ScoreOut` больше не содержит поля `value_smooth`.
- В запросах `/scores*` сохраняется `value_raw = COALESCE(scores.raw_value, scores.value)`.
- Время события = `scores.measured_at`, маппится на `occurred_at` для совместимости API.

### 3) Profiles
- Для `charts` и `disc_profile` остаётся явный `501 Not Implemented`.
- Поддерживаются только `header`, `tracks`, `full` (как и требуется hotfix-скоупом).

## Что удалено
- Создание таблиц `metric_groups`/`metric_group_members` в bootcheck.
- Любые агрегации/статистика по группам метрик на старой схеме.
- Поле `value_smooth` из DTO и вычисления сглаживания в репозитории оценок.

## Что упрощено
- Bootcheck теперь проверяет только наличие ключевых таблиц и делает один write-тест.
- Возврат оценок в `/scores*` — только реальные значения без пост-обработки.

## Что оставлено как legacy/compat
- Поле `occurred_at` в API сохраняется как совместимость и маппится на `scores.measured_at`.
- `tracks.start_at` / `tracks.end_at` продолжают возвращаться как `NULL` (без фильтрации по датам).

## Проверки
- Выполнена компиляционная проверка модулей Python (`python -m compileall server`).

