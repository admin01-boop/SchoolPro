# Project instructions

Django REST backend (`backend/`) + React/Vite frontend (`frontend/`). Layout, conventions and production notes: [README.md](../README.md). Business rules: [spec.md](../spec.md).

- Business rules live in spec.md. When a change adds or modifies a rule (permissions, validation, settings, feature status), update spec.md in the same change and remove outdated lines.
- Keep spec.md short: rules and decisions only, not field lists or code details.

## Commands (Windows, PowerShell 5.1)

- Backend tests: `.\.venv\Scripts\python.exe backend\manage.py test accounts academics students core staff` (one module: append e.g. `academics.tests.test_classrooms`).
- Frontend tests: `npm.cmd --prefix frontend run test`. Always call `npm.cmd`, not `npm`.
- Lint: `.\.venv\Scripts\python.exe -m ruff check backend` and `npm.cmd --prefix frontend run lint`.
- Run the app: `powershell -ExecutionPolicy Bypass -File .\scripts\start-app.ps1` (migrates, then starts backend :8000 and frontend :5173).
- Use `[IO.File]::WriteAllText` rather than `Set-Content -NoNewline` (unsupported in 5.1).

## Conventions and pitfalls

- Backend views are thin; logic goes in `<app>/services.py`. Endpoints live under `/api/v1/`.
- Frontend: one folder per screen under `features/` with tests in `__tests__/`; all HTTP goes through `@/lib/apiClient` (`@` = `frontend/src`).
- Role data goes in a profile table linked to `accounts.User`, never as new columns on `User`.
- Keep exactly one `AcademicYear` with `is_current=True`; otherwise roster grade/status silently come back empty.
- Token auth must stay ahead of session auth and `LoginView` ignores sessions; a stale Django admin cookie otherwise causes 403 on API calls.
- Do not switch the dev database from SQLite or change the admin password without an explicit request.
