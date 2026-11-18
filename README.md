# PomoTrack

A backend API for a task tracker with Pomodoro sessions. Users register, create
categories and tasks, log work and break sessions, and see their statistics.
Every user sees only their own data.

## Stack

Python 3.12, FastAPI, SQLModel, PostgreSQL, Alembic, JWT (PyJWT, pwdlib/argon2),
pytest, Docker Compose, uv.

## Features

- Registration and login with JWT (OAuth2 password flow)
- Tasks and categories: CRUD, filtering, search, sorting, pagination
- Pomodoro sessions (work, short break, long break) with time validation
- Statistics: summary for a period and time per category
- Per-user data isolation
- Per-user timer settings (work/break durations)
- Automated tests and CI

## Quick start (Docker)

    cp .env.example .env
    docker compose up --build

The API is at http://localhost:8000, interactive docs at http://localhost:8000/docs.
Database migrations are applied automatically when the `api` container starts.

## Run locally (without Docker for the API)

    cp .env.example .env
    docker compose up -d db
    uv sync
    uv run alembic upgrade head
    uv run uvicorn app.main:app --reload

## Run tests

    uv run pytest

Tests use an in-memory SQLite database, so they never touch your real data.

## Endpoints

All endpoints except `/auth/*` require `Authorization: Bearer <token>`.

| Group | Method | Path | Description |
|---|---|---|---|
| Auth | POST | /auth/register | Create an account |
| Auth | POST | /auth/token | Log in, get a JWT |
| Users | GET | /users/me | Current user |
| Users | GET, PATCH | /users/me/settings | Timer settings |
| Categories | GET, POST | /categories/ | List / create |
| Categories | GET | /categories/{id}/tasks | Tasks of a category |
| Categories | DELETE | /categories/{id} | Delete (409 if it has tasks) |
| Tasks | GET, POST | /tasks/ | List with filters / create |
| Tasks | GET, PUT, PATCH, DELETE | /tasks/{id} | One task |
| Tasks | GET | /tasks/{id}/sessions | Sessions of a task |
| Sessions | GET, POST | /sessions/ | List with filters / create |
| Sessions | DELETE | /sessions/{id} | Delete a session |
| Stats | GET | /stats/summary | Totals for a period |
| Stats | GET | /stats/by-category | Minutes per category |

## Design decisions

- **404 instead of 403 for other users' data.** A 403 would confirm that the
  object exists. With 404, someone else's task looks the same as a missing one.
- **`user_id` comes from the token, never from the request body.**
- **All times are stored and compared in UTC.**
- **Unique category names per user**, not globally (a composite constraint).
- **A category with tasks cannot be deleted** (409).
- **Sessions when a task is deleted:** <write your decision here>
- **Migrations run on container start**, so a new user needs only two commands.
- **Same error text for wrong login and wrong password**, and a dummy hash check,
  so an attacker cannot learn which usernames exist.