# Ревизия кода под новую схему БД (2026-01-27)

## Контекст
В репозитории используется схема `db/schema/current_schema.sql`. Сейчас актуальна новая схема `db/schema/new_schema.sql`, где изменились таблицы метрик/оценок и поля в треках. Ниже — ревизия, что сломается, что нужно адаптировать и детальное ТЗ для разработчика.

## Ключевые отличия схемы (важные для сервера)

### 1) `step_metric_scores` → `scores`
* Было: `step_metric_scores` с обязательным `step_id` и полем `value`.
* Стало: `scores`, где:
  * `track_id` обязателен.
  * `step_id` опционален (оценка больше не обязана быть привязана к шагу трека).
  * Введены `raw_value`, `corrected_value`, `value`, `measured_at`, `attached_at`, `computed_at`, `value_version`, `value_source`.
  * `role_at_rate` теперь **обязателен**.

Следствия: все запросы/DTO, которые завязаны на `step_metric_scores` и `track_steps.occurred_at`, перестают работать. Нужен переход на `scores` и корректное время события (см. раздел «Что адаптировать»).

### 2) `metrics` поменялась по структуре
* Было: `metric_id`, `name`, `metric_type`, `definition`, `anchors_json`.
* Стало: `metric_id`, `kind`, `name`, `system`, `code`, `members_json`, `definition`.
* Таблицы `metric_types`, `metric_groups`, `metric_group_members` исчезли.

Следствия: список метрик и типы метрик для справочников/эндпойнтов нужно менять — в коде ожидается поле `metric_type` и таблица `metric_types`, их больше нет.

### 3) Треки без `start_at` и `end_at`
* В новой схеме таблица `tracks` не содержит `start_at` и `end_at`.

Следствия: любые запросы, которые фильтруют активные треки по временным окнам, или возвращают эти поля, ломаются. Логика определения активных треков должна быть пересмотрена.

### 4) Новые таблицы
* `bot_state` — состояние бота, ранее отсутствовало.
* `profiles` — материализованные профили/вычисленные данные.

В коде этих таблиц сейчас нет, поэтому они **не ломают** приложение, но есть возможность интеграции позже.

## Что сломается при переходе на новую БД

1) **Все SQL-запросы к `step_metric_scores`**
   * В `scores_repo` используется `step_metric_scores` и обязательный join с `track_steps` (по `step_id`), а также фильтрация по `ts.occurred_at`.
   * В новой схеме таблицы нет, join не с чем, фильтры по времени требуют переезда на поля `scores.*_at`.

2) **Проверка при старте (bootcheck) в `main.py`**
   * Создание `metric_groups`/`metric_group_members` в рантайме и сбор статистики по `step_metric_scores`.
   * В новой схеме эти таблицы отсутствуют, запросы упадут.

3) **Справочники метрик**
   * `reference_repo.list_metrics()` ожидает `metric_type`.
   * `reference_repo.list_metric_types()` читает таблицу `metric_types`.
   * В новой схеме ни поля, ни таблицы нет.

4) **API-модели для метрик и треков**
   * `MetricOut.metric_type` больше не заполняется.
   * `TrackSummaryOut.start_at/end_at` больше нельзя вернуть.

5) **Логика активных треков и окна сглаживания в `scores_service`**
   * `tracks_repo` и `scores_service` читают `start_at/end_at` (а также фильтруют по ним).
   * Новая схема не содержит этих полей → ошибка на SELECT.

## Что адаптировать в проекте (предлагаемые изменения)

### A) Перевести работу с оценками на `scores`
* Обновить `scores_repo`:
  * заменить таблицу `step_metric_scores` на `scores`.
  * убрать обязательный `JOIN track_steps` (оставить `LEFT JOIN` при наличии `step_id`).
  * заменить `ts.occurred_at` на `scores.measured_at` (или `attached_at`, если нужна дата привязки).

**Вопрос к бизнес-логике:** что считать временем измерения:
* `measured_at` (момент измерения),
* или `attached_at` (момент прикрепления к шагу),
* или `computed_at` (момент вычисления итогового значения).

Решение нужно зафиксировать и использовать в фильтрах `since/until` и для сортировки.

### B) Обновить `ScoreOut` и схему ответа
* Сейчас API возвращает `value_raw` и `value_smooth`. Это должно соответствовать новым колонкам:
  * `value_raw` ← `scores.raw_value`.
  * `value_smooth` — по прежней логике сглаживания (остается вычисляемым полем).
* Нужно добавить/обсудить дополнительные поля, если они важны для клиента:
  * `corrected_value`, `value` (финальная оценка),
  * `measured_at`, `attached_at`.

### C) Обновить логику сглаживания
* Сейчас `scores_service` берет окно по `track.start_at/end_at`. Теперь их нет.
* Варианты:
  1. Строить интервал только по входным `since/until` (если не переданы — использовать `now` и `now - N дней`).
  2. Использовать `scores.measured_at` как источник диапазона по факту данных.
  3. Если в будущем вернется трековое окно — добавить новую таблицу/поля.

Нужна явная бизнес-договоренность, какой вариант правильный.

### D) Справочники метрик
* Переехать на новые поля `metrics.kind/system/code`.
* Убрать эндпойнт `metric_types` или заменить:
  * например, `MetricTypeOut` = `kind` (`metric`/`group`).
  * если нужен список типов — брать `SELECT DISTINCT kind FROM metrics`.
* В `MetricOut` заменить `metric_type` на `kind` (или оставить старое поле, но переименовать в API).

### E) Удалить/заменить runtime-таблицы метрик в bootcheck
* Удалить создание `metric_groups`/`metric_group_members`.
* Если нужны групповые метрики — теперь это `metrics.kind='group'` + `members_json`.
* Если нужна статистика по группам — читать `members_json` и агрегировать через JSON-функции (DuckDB поддерживает JSON).

### F) Треки и активность
* Обновить `tracks_repo`:
  * убрать `start_at/end_at` из SELECT.
  * пересмотреть фильтры активности: только `status='active'` или новая бизнес-логика.
* Обновить `TrackSummaryOut` — убрать `start_at/end_at` (или делать nullable и не заполнять).

## Подробное ТЗ программисту по адаптации проекта

1) **Слой БД (`server/db`)**
   - `scores_repo.py`:
     1. заменить `step_metric_scores` на `scores`.
     2. поля:
        * `sms.value` → `scores.raw_value` (или `scores.value` — выбрать официальное значение).
        * `ts.occurred_at` → `scores.measured_at` (или согласованное поле времени).
     3. `JOIN track_steps` сделать `LEFT JOIN` или убрать, так как `step_id` может быть `NULL`.
     4. критерии фильтрации по времени — использовать выбранное поле времени из `scores`.
   - `reference_repo.py`:
     1. заменить `metric_type` на `kind`.
     2. удалить `list_metric_types()` или заменить на выборку `SELECT DISTINCT kind FROM metrics`.
   - `tracks_repo.py`:
     1. убрать `start_at`, `end_at` из SELECT/WHERE.
     2. пересмотреть фильтрацию `active_only`: либо статус, либо новая бизнес-логика.
     3. `get_track_window` — либо удалить, либо заменить на использование `scores.measured_at`.

2) **Сервисы (`server/services`)**
   - `scores_service.py`:
     1. адаптировать чтение времени (`occurred_at`) под новое поле.
     2. изменить источник окна (нет `start_at/end_at`).
     3. если оценки без шага — исключить зависимость от `track_steps`.
   - `reference_service.py`:
     1. синхронизировать с обновленной моделью метрик.

3) **Схемы API (`server/schemas`)**
   - `scores.py`:
     1. заменить `step_id: str` на `step_id: Optional[str]`.
     2. добавить/обновить поля в соответствии с новой схемой (`raw_value`, `corrected_value`, `value`, `measured_at`, `attached_at`).
   - `reference.py`:
     1. `MetricOut.metric_type` → `kind` (или оставить поле, но маппить `kind`).
     2. решение по `MetricTypeOut` — либо удалить эндпойнт, либо выдавать `kind`.
   - `tracks.py`:
     1. убрать `start_at` и `end_at` из DTO, если в API они больше не нужны.

4) **Bootcheck (`server/main.py`)**
   - убрать создание `metric_groups`/`metric_group_members`.
   - заменить статистику по группам на логику `metrics.kind='group'` + `scores`.

5) **Регрессионные проверки**
   - пройтись по основным эндпойнтам:
     * `/scores/track/{track_id}`
     * `/scores/student/{student_id}`
     * `/scores/query`
     * `/scores/series` (если используется)
     * `/reference/metrics`
   - убедиться, что фильтры по времени и сортировка работают с новым полем времени.

6) **Дополнительные решения (согласовать заранее)**
   - какое поле является «истинной датой» оценки (`measured_at` vs `attached_at` vs `computed_at`).
   - какой тип метрик нужен клиенту (`kind` vs старый `metric_type`).
   - как трактовать «активность» трека без `start_at/end_at`.

---
Если нужно, могу подготовить отдельный diff-план или патч по пунктам выше.
