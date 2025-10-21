# Scores API snippets

Примеры вызовов для проверки новых эндпоинтов.

```bash
# Оценки по треку
curl -s "https://neiruha.space/api/v1/scores/track/track_42c955b282ea4cad?limit=50" \
  -H "Authorization: Bearer phil_token_zxcvbnhjaks" | jq

# С фильтрами
curl -s "https://neiruha.space/api/v1/scores/track/track_42c955b282ea4cad?student_id=u_cfa5319f2a3abaafc8987847&metric_id=m_disc_01&since=2025-10-01T00:00:00&until=2025-11-01T00:00:00" \
  -H "Authorization: Bearer phil_token_zxcvbnhjaks" | jq

# Оценки ученика
curl -s "https://neiruha.space/api/v1/scores/student/u_cfa5319f2a3abaafc8987847?limit=100" \
  -H "Authorization: Bearer phil_token_zxcvbnhjaks" | jq

# Массовый запрос
curl -s "https://neiruha.space/api/v1/scores/query" \
  -H "Authorization: Bearer phil_token_zxcvbnhjaks" \
  -H "Content-Type: application/json" \
  -d '{
    "track_ids": ["track_42c955b282ea4cad","track_c61a58ed773a4110"],
    "student_ids": ["u_cfa5319f2a3abaafc8987847"],
    "metric_ids": ["m_disc_01","m_disc_02"],
    "since": "2025-10-01T00:00:00",
    "until": "2025-11-01T00:00:00",
    "limit": 1000,
    "offset": 0
  }' | jq

# Переименование пользователя
curl -s -X PATCH "https://neiruha.space/api/v1/users/u_cfa5319f2a3abaafc8987847" \
  -H "Authorization: Bearer phil_token_zxcvbnhjaks" \
  -H "Content-Type: application/json" \
  -d '{ "display_name": "Фил-легенда" }' | jq

# Переименование трека
curl -s -X PATCH "https://neiruha.space/api/v1/tracks/track_42c955b282ea4cad" \
  -H "Authorization: Bearer phil_token_zxcvbnhjaks" \
  -H "Content-Type: application/json" \
  -d '{ "title": "Геймдизайн PRO" }' | jq
```
