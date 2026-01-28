# 2026-01-28 API cleanup (tracks/messages/reference/users/scores/profiles)

## Summary
- Removed the Tracks HTTP router and unregistered it from the API router to reduce external surface area.
- Removed the legacy profiles endpoint and kept the supported `/profiles/by-user` and `/profiles/by-telegram` endpoints.
- Simplified the Users API to a single `GET /api/v1/users` endpoint with optional `role` filtering.
- Consolidated reference lookups into a single `POST /api/v1/ref` endpoint and removed individual reference routes.
- Reduced Scores API to only `POST /api/v1/scores/query` and enabled client access.

## Router changes
- Deleted `routers/tracks.py` and removed its registration from `routers/__init__.py`.
- Deleted `routers/reference.py`, added `routers/ref.py`, and registered it in `routers/__init__.py`.
- Updated `routers/users.py` to expose only a single list endpoint with optional `role`.
- Updated `routers/scores.py` to keep only the query endpoint and allow client tokens.
- Updated `routers/profiles.py` to remove the legacy endpoint.

## Service/schema adjustments
- Removed unused user info/rename service logic and schema models tied to the removed endpoints.
- Added request/response schemas for the unified `/ref` endpoint.
- Trimmed service exports to match the simplified API surface.

## Notes
- Tracks data remains accessible through `/profiles/by-user/{user_id}?profile_type=tracks|full`.
- No database schema changes were made.
