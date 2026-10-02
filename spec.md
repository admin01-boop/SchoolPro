# Managbac - Specification

School management system for Southbridge International School Cambodia (SISC): a Django REST backend and a React frontend. This file records the rules that are not obvious from the code. See [README.md](README.md) for setup and folder layout.

## 1. Users and roles

One login table, `accounts.User`, with a `role`: `STUDENT`, `TEACHER`, `PARENT`, `OBSERVER`, `ADMIN`, `STAFF`.

| Role | Profile table | API access today |
|---|---|---|
| ADMIN (and superusers) | `staff.AdminProfile` | Full management API (`IsStaffRole`) |
| STAFF (non-teaching school staff) | `staff.StaffMember` | Full management API (`IsStaffRole`) |
| TEACHER | `staff.Teacher` | None yet |
| PARENT | `students.Guardian` | Linked children only (`GET /me/children/`, `IsParent`) |
| STUDENT | `students.Student` | Own record only (`GET /me/student/`, `IsStudent`) |
| OBSERVER | `staff.Observer` | None yet |

- Only ADMIN/STAFF can use the management API. Students can read their own record and parents can read their linked children. TEACHER and OBSERVER do not yet have API access.
- The frontend routes each role to its own home URL: `/admin/home`, `/student/home`, `/parent/home`, `/teacher/home`, `/observer/home`, or `/staff/home`. Teacher, observer and staff homes initially show username and role. `/me` redirects to the signed-in user's home. STAFF still passes the management API permission but has no management screens. The API enforces access; the routing is only for usability. An admin can preview any role from the menu dropdown (UI only).
- A student's own record is resolved from the login (`Student.user`), never from a URL id. It omits staff-only fields such as remarks, and shows guardians only when Parents Association is on. A student login with no linked `Student` gets 404.
- A parent sees only their linked children (`GET /me/children/`, `IsParent`; resolved from `Guardian.user`); the list is empty when Parents Association is off.
- Existing students without a login get one from `manage.py create_student_logins --domain <d>` (username `<student_id>@<d>`, random password written to a CSV; re-runnable).
- Only an ADMIN or superuser may create or edit an ADMIN account.
- Only an ADMIN or superuser may set another user's password or require a password change at next login. Accounts marked for a change can only use the password-change and logout endpoints until they choose a valid new password.
- New users default to `OBSERVER` (no API access); `createsuperuser` defaults to `ADMIN`. Roles that grant management access must be chosen explicitly.
- Teacher, staff, observer and admin users always get their profile row, created automatically by a `post_save` signal in `staff/signals.py` however the user was created (roster, Django admin, command line).
- A person has one `User` row and one role. Role-specific data lives in a profile table linked one-to-one to `User`, never as extra columns on `User`.
- Profile links on `Student` and `Guardian` are nullable, so records can exist before a login does (for example imported from the master list).

## 2. Authentication and security

- Login: `POST /api/v1/auth-token/` returns a token. Limited to 5 attempts/minute (`THROTTLE_LOGIN`).
- Tokens expire after 12 hours (`AUTH_TOKEN_TTL_HOURS`); an expired token is deleted and the user must sign in again. Logout: `POST /api/v1/auth/logout/` deletes the token.
- Token authentication is checked before session authentication. Otherwise a leftover Django admin session cookie (cookies are shared across ports on `localhost`) forces CSRF on API calls and they fail with 403.
- The login endpoint ignores sessions entirely for the same reason.
- The frontend keeps the token in `sessionStorage` and signs the user out on any 401.
- All frontend pages require sign-in except `/login`. Signed-in users are redirected away from `/login`, and unknown paths redirect to `/`.
- Production (`config.settings.prod`) requires `SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`.
- Changes to `User`, `Student` and `Enrollment` are recorded with the acting user (`Model.history`). Password hashes and `last_login` are not recorded.

## 3. Academic rules

- **Current academic year:** at most one `AcademicYear` has `is_current=True` (database constraint). Saving a year as current demotes the previous one. If no year is current, roster grade and status come back empty, so keep one set.
- **Grade numbering:** each academic year chooses `YEAR_12_13` (default; names as stored) or `GRADE_11_12` (Year 7 shows as Grade 6, and so on). The mapping table is in `academics/labels.py`. Names are display-only; the canonical `YearLevel` is the stored identity.
- **Key Academic Functions** (one settings row):
  - `classes_enabled`: when off, classes can only be created, changed or deleted for the Diploma Programme (DP).
  - `parents_association_enabled`: when off, guardian endpoints return 403, guardian counts show 0, and parents cannot be linked to students.
  - Also stored: annotations, term grade calculation (percentage or absolute), points-based averaging, year-level behaviour.
- **Curricula:** an `AcademicCurriculumOption` must be enabled to appear. Enabling one creates its framework, track and a `Curriculum`, and a mapping row (disabled by default) for every year level. A `Curriculum` saved through the API must be linked to at least one enabled option.
- **Years & Levels grid:** a `GradeLevelTrackMapping` row says whether a year level is offered on a track. A `GradeLevel` can be assigned to a student only if its year level is enabled on at least one enabled track (`assignable_grade_level_ids`). Saving the grid reports enabled cells that have no grade levels linked.

## 4. Student and enrollment rules

- `Student` holds data that does not change by year (IDs, names, date of birth, nationality). `student_id` is unique; `frn` groups siblings.
- `Enrollment` is one student in one academic year. Unique per student, year and `is_trial`. Statuses: New Enrollment, Existing, Returned Student, Withdrawn. History lives here, not on `Student`.
- An enrollment's grade level must be assignable (see section 3); its curriculum must be enabled.
- Parents are `Guardian` records shared across siblings through `StudentGuardian` (relationship, legal custody).
- Roster grade filter: `GET /students/?filter_active=true` filters by each student's grade in the current academic year. `grade_level` can repeat; `include_no_grade` (default true) controls whether students with no grade appear.
- Adding a user with the Student type requires student ID, sex and date of birth. It creates the `User`, `Student` and, if a current year exists, a New Enrollment. Parent type creates a `Guardian`; the Teacher, Staff, Observer and Admin types get their profile from the signal above.
- New accounts use their (required, unique) email, lowercased, as the username. They get a random 20-character password. It is emailed if email is configured and requested; otherwise it is returned once in the response.
- Roster tabs read each type's own table: Students `GET /students/`, Teachers `GET /roster-teachers/` (`staff.Teacher`), Staff `GET /roster-staff/` (`staff.StaffMember`), Parents `GET /roster-parents/` (`Guardian`, including those without a login; not gated by Parents Association). Observers `GET /roster-observers/` (`staff.Observer`), Admins `GET /roster-admins/` (`staff.AdminProfile`). All are searchable and paginated. A user without a profile row does not appear on its role's tab.
- Every roster row is edited by clicking the person's name, which opens an edit form. Teacher, Staff, Observer and Admin rows use `PATCH /roster-<role>/<id>/`: the profile fields plus the login user's first name, last name and e-mail; changing the e-mail also changes the username, and it must be unique. Parent rows use `PATCH /roster-parents/<id>/` (name and phones; works for parents without a login and when Parents Association is off). Student rows use `PATCH /students/<id>/`. The `/roster-<role>/` endpoints are list and PATCH only. A blank employee ID is stored as NULL (it is unique). Only an admin may edit an admin.

## 5. API conventions

- Django REST Framework, JSON, versioned under `/api/v1/`; breaking changes go to `/api/v2/`.
- Default permission is `IsStaffRole`. Pagination is 25 per page (`page_size` up to 100). Search with `?search=`.
- Errors use DRF's shape (`detail` or per-field lists). Unexpected errors return `{"detail": "Internal server error."}` and are logged.
- Views are thin; business logic is in each app's `services.py`.

## 6. Status and roadmap

Built:
- Login and logout.
- School Directory > Roster: list, search, grade filter, add user.
- Settings > Key Academic Functions.
- Settings > Years & Levels.
- Student portal (read-only own record).
- Django admin for all models.

Not built:
- Teacher workflows and expanded staff/observer tools; student grades, attendance and any editing.
- Other sidebar items (inert placeholders).
- Export endpoints.
- Teacher assignments to classes and subjects.

Open decisions:
- PostgreSQL migration. Local development still uses SQLite.
- Whether one person may hold several roles (currently one `role` per account).
- Whether to add CI and a Dockerfile (deferred).

## 7. Development conventions

- Models are the source of truth for field types, nullability and indexes. Request/response shapes come from the code and tests, not from this file.
- Business logic goes in `<app>/services.py`; views only handle HTTP.
- Choose `on_delete` deliberately: `PROTECT` for historical records (an enrollment's academic year), `CASCADE` for owned child rows, `SET_NULL` for optional links.
- Every model change ships with its migration. Every new endpoint or rule change ships with tests.
- Tests use Django's test runner, one module per concern in each app's `tests/`. List endpoints must not run a query per row (`students/tests/test_query_counts.py` guards this).
- The frontend sends the API's `snake_case` keys unchanged. All HTTP goes through `request()` in `frontend/src/lib/apiClient.js`.
- Each frontend screen lives in `frontend/src/features/<name>/` with its tests in `__tests__/`.
- Configuration comes from environment variables (`backend/.env`); new variables are added to `.env.example`.
