## [2025-10-25 00:11] Codex Auto-Update
- добавлены эндпоинты users/teachers, users/mentors, users/students
- добавлен раут profiles/by-user/{user_id}
- добавлено поле roles в UserInfoOut
- сгенерирован .env шаблон в /todo

## [2025-10-27 00:15] Startup reliability improvements
- added a startup log separator and an explicit "Yoohoo, we are launching..." message to highlight the boot phase
- safe-check failures (including DuckDB lock conflicts) now stop the server with an emotional "oh, how sad, but I cannot continue working" log entry
- documented the behavior update here
