# SchoolPro

Managbac (SISC School Management)

Django REST backend + React (Vite) frontend. Business rules and roadmap: [spec.md](spec.md).

## Run

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-app.ps1
```

Starts the backend on http://127.0.0.1:8000 and the frontend on http://localhost:5173 (migrates the DB first).

## Layout

```
backend/
  config/        project package: settings/{base,dev,prod}.py, urls.py, api_urls.py (mounted at /api/v1/)
  core/          shared API pieces: pagination, exception handler
  accounts/      User model, token login/logout (expiring tokens, throttled), role permissions
  academics/     years/levels, curricula, classrooms
  staff/         Teacher, StaffMember, Observer and AdminProfile (one-to-one with User)
  students/      students, guardians, enrollments, roster
    api/         views.py, serializers.py, urls.py (HTTP layer only)
    services.py  business logic called by the views
    tests/       one test module per concern
frontend/src/
  app/           App.jsx (providers + routes)
  features/      one folder per feature: page, components, tests (auth, roster, years-levels, key-academic-functions)
  components/    shared UI (Sidebar, ErrorBoundary)
  layouts/       page shells
  lib/           apiClient.js (all HTTP goes through request())
  styles/        global CSS
scripts/         start-app.ps1, backup-db.ps1 (PostgreSQL dump)
.vscode/         debug configs (Django, tests, Chrome) and tasks
```

`@` is an alias for `frontend/src` (e.g. `import { request } from '@/lib/apiClient'`).

## Conventions

- Views stay thin; put business logic in `<app>/services.py`.
- New backend endpoints go under `/api/v1/`; breaking changes need `/api/v2/`.
- New frontend screens get their own folder under `features/` with tests in `__tests__/`.
- Settings: `manage.py` uses `config.settings.dev`; `wsgi`/`asgi` use `config.settings.prod`, which requires `SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`. Override with `DJANGO_SETTINGS_MODULE`.
- One login table (`accounts.User`, `role` field) plus a profile table per role that has its own data (`Student`, `Guardian`, `Teacher`, `StaffMember`, `Observer`, `AdminProfile`). Add a new profile table rather than columns on `User`.
- Role gates: `IsStaffRole` is the API default; use `IsTeacher`/`IsParent`/`IsStudent` or `role_required(...)` from `accounts.permissions` for new portals.
- Only one `AcademicYear` can be current (database constraint); saving a year as current demotes the previous one.
- Audit trail: `User`, `Student` and `Enrollment` keep history (django-simple-history). Read it via `Model.history`. After first deploy of history, run `manage.py populate_history --auto` once to seed existing rows.

## Tests and lint

```powershell
.\.venv\Scripts\python.exe backend\manage.py test accounts academics students core staff
npm.cmd --prefix frontend run test

.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt   # ruff, pip-audit
.\.venv\Scripts\python.exe -m ruff check backend
npm.cmd --prefix frontend run lint

# dependency security checks
.\.venv\Scripts\python.exe -m pip_audit -r backend\requirements.txt
npm.cmd --prefix frontend audit
```

## Production notes

- Use PostgreSQL: `pip install -r backend\requirements-postgres.txt`, then set `DATABASE_URL=postgres://user:pass@host:5432/db` in `backend/.env` and run `manage.py migrate`. To move existing SQLite data: `dumpdata --natural-foreign --exclude contenttypes --exclude auth.permission` then `loaddata`.
- Back up with `scripts\backup-db.ps1` (needs `pg_dump` on PATH) and test a restore before relying on it.
- Tokens expire after `AUTH_TOKEN_TTL_HOURS` (default 12). Login is limited to `THROTTLE_LOGIN` (default 5/min). Throttle counters use the in-process cache, so use a shared cache (Redis) when running several workers.
- Change the default admin password with `manage.py changepassword admin` before exposing the app.

## Debugging

- Backend logs go to the console; set `LOG_LEVEL=DEBUG` in `backend/.env`. API 4xx are logged at INFO and 5xx with a traceback under the `api` logger.
- Unexpected backend errors return JSON `{"detail": "Internal server error."}`.
- Frontend API errors are `ApiError` (`message`, `status`, `body`); a top-level error boundary catches render crashes.
- Use the launch configs in `.vscode/launch.json`.
