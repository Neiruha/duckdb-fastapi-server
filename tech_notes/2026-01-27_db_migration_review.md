# DB migration review (2026-01-27)

## 1) Сравнение current_schema.sql vs new_schema.sql (только то, что реально затрагивает код)
- Таблица оценок: `step_metric_scores` → `scores`, добавлен `measured_at`, `raw_value`, `value`, `corrected_value`, `step_id` теперь nullable, и `track_id` хранится прямо в `scores` (вместо джойна через `track_steps`).
- Таблица `metrics`: вместо `metric_type` появились поля `kind`, `system`, `code`, `members_json`.
- Таблица `metric_types` удалена; в новой схеме справочник типов метрик нужно формировать из `metrics.kind`.
- Таблица `tracks`: поля `start_at` / `end_at` отсутствуют — код не должен использовать окно трека.
- Новая таблица `profiles` добавлена (можно пока собирать данные «на лету»).

## 2) Что сломается (точки в коде, если оставить старую схему)
- `server/db/scores_repo.py`: все запросы читают `step_metric_scores` и фильтруют по `track_steps.occurred_at`.
- `server/services/scores_service.py`: smoothed-series зависит от окон трека `start_at/end_at`, интервалов и рядов на основе `track_steps`.
- `server/routers/scores.py` и `server/schemas/scores.py`: ожидают smoothed-series и `occurred_at` из `track_steps`.
- `server/db/reference_repo.py` + `server/schemas/reference.py`: используют `metrics.metric_type` и таблицу `metric_types`.
- `server/db/tracks_repo.py`: фильтрация `start_at/end_at` и выборка этих полей.
- `server/main.py` (startup_safe_check): статистика групп метрик основана на `step_metric_scores`.

## 3) Что адаптировать (план по слоям)
- **repo**:
  - `scores_repo`: заменить `step_metric_scores` на `scores`, использовать `scores.measured_at` как время; учитывать `step_id` nullable; брать `raw_value` как `value_raw`.
  - `tracks_repo`: убрать фильтрацию по `start_at/end_at`, вернуть `NULL AS start_at/end_at` для совместимых DTO.
  - `reference_repo`: вернуть новые поля `metrics` и заменить `/metric-types` на `SELECT DISTINCT kind`.
  - `main.py`: заменить статистику по `step_metric_scores` на `scores` (колонка `raw_value`).
- **service**:
  - `scores_service`: убрать smoothed-series; добавить `/scores/user/{user_id}` на основе `scores`.
  - `profiles_service`: добавить новый API типов `header|tracks|full`, planned: `charts|disc_profile`.
- **router**:
  - `scores`: удалить `GET /scores/smoothed-series`, добавить `GET /scores/user/{user_id}`.
  - `profiles`: расширить `/profiles/by-user/{user_id}` параметром `type`.
- **schemas**:
  - `scores`: `step_id` nullable, `occurred_at` берется из `measured_at`.
  - `reference`: обновить поля `MetricOut`.
  - `profiles`: добавить модели для `header/tracks/full`.

## 4) Риски и решения
- **Какое поле считать временем оценки?**
  - Решение: использовать `scores.measured_at` как canonical time (в ответе `occurred_at` = `measured_at`).
- **`step_id` nullable**
  - Решение: не джойнить `track_steps`, а читать `scores.track_id` напрямую.
- **Справочник `metric_types` отсутствует**
  - Решение: `GET /reference/metric-types` возвращает DISTINCT `metrics.kind`.
- **Сглаживание больше не нужно**
  - Решение: удалить smoothed-series; поле `value_smooth` возвращается как clamp(raw) для совместимости.
- **Планируемые типы профиля**
  - `charts` и `disc_profile` зарезервированы: запросы этих типов должны отвечать `501 Not Implemented`.

## 5) Чеклист регресса (ручной/тесты)
- `/health`
- `/dbalive`
- `/reference/metrics`
- `/reference/metric-types`
- `/scores/track/{track_id}`
- `/scores/student/{student_id}`
- `/scores/query`
- `/scores/user/{user_id}`
- `/profiles/by-user/{user_id}?type=header`
- `/profiles/by-user/{user_id}?type=tracks`
- `/profiles/by-user/{user_id}?type=full`
- `/profiles/by-user/{user_id}?type=charts` (ожидаем 501)
