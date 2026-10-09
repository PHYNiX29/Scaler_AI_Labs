# Typeform clone

A form builder modelled on Typeform: build a form in a drag-and-drop builder with a live preview, publish it to a public link, collect answers one question at a time, and review the results.

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 16 (App Router, TypeScript), Tailwind CSS 4, lucide-react icons |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2, Pydantic 2 |
| Database | SQLite (single file) |
| Tests | pytest + FastAPI TestClient |

## Run it locally

Backend (http://localhost:5000, interactive API docs at `/docs`):

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 5000 --reload
```

No backend `.env` is needed for local use. `backend/.env.example` lists the two optional variables (`DATA_DIR`, `CORS_ORIGINS`); set them in your shell or host if you want to change the defaults.

The first start creates `backend/data/typeform.db` and seeds it with two published forms and sample responses. Delete that file to reseed.

Frontend (http://localhost:3000):

```bash
cd frontend
npm install
cp .env.example .env.local     # Windows cmd: copy .env.example .env.local
npm run dev
```

Tests:

```bash
cd backend
pytest
```

Useful URLs: `/dashboard` (forms list), `/to/customer-feedback` (a seeded form with branching), `/to/ai-summit-rsvp`.

## Architecture

```
frontend/src
  app/                     routes: / (landing), /dashboard, /forms/[id]/edit (builder), /to/[slug] (public form)
  components/
    question/              QuestionView + AnswerInput: one page of a form, used by BOTH the builder canvas and the respondent flow
    respondent/            RespondentFlow: page-by-page state machine (fade transitions, keyboard, progress, submit)
    builder/               header, pages sidebar (drag-and-drop), settings panel, design panel, logic editor, workflow diagram, share, results
    dashboard/             forms list with create / rename / duplicate / publish / delete
    ui/                    toasts, modal, toggle, menu
  lib/api.ts               typed fetch client for every endpoint
  lib/respondent.ts        client-side validation + a mirror of the branching engine (builder preview only)

backend/app
  main.py                  app, CORS, startup (create tables + seed), static /uploads
  config.py, database.py   settings from env; engine, session and the "current user" dependency
  models/                  SQLAlchemy models (schema below)
  schemas.py               Pydantic request bodies
  routes/                  form_routes (forms + questions), public_routes (respondent), response_routes (results), upload_routes
  services/                validator (answer rules), logic_engine (branching), stats_service (summaries)
  utils/seeder.py          sample data
```

Key decisions:

- **One component renders a question everywhere.** The builder canvas, the preview and the public form all use `QuestionView`, so the creator edits exactly what the respondent sees.
- **The server is the authority on validation and branching.** The client validates for instant feedback, then asks `validate-step` where to go next. On submit the server re-walks the branching from the submitted answers (`walk_path`) and validates only the questions on that path, so a required question skipped by a jump does not block the submit, and a client cannot skip validation.
- **Branching rules live on the question** as `logic_jumps`: `[{choice_id, target_question_id}]`. Rules are keyed by choice id, so renaming a choice does not break them. A rule whose target was deleted falls back to the normal order.
- **Builder edits are optimistic and debounced**: the UI updates immediately and saves 500 ms after the last change.
- **Everything persistent lives in one folder** (`DATA_DIR`): the SQLite file and uploaded media. That folder is a mounted volume in production.

## Database schema

```
users      id PK, email UNIQUE, name, created_at, updated_at
forms      id PK, user_id FK -> users, title, description, slug UNIQUE, status (draft|published),
           views_count, submissions_count, theme_settings JSON, created_at, updated_at
questions  id PK, form_id FK -> forms (cascade), order_index, question_type, title, description, required,
           properties JSON, media JSON, logic_jumps JSON, created_at, updated_at
responses  id PK, form_id FK -> forms (cascade), session_id, ip_address, user_agent,
           status (in_progress|completed), started_at, submitted_at, time_taken_seconds
answers    id PK, response_id FK -> responses (cascade), question_id FK -> questions (cascade),
           question_type, value JSON, created_at
```

Relationships: a user has many forms; a form has many ordered questions and many responses; a response has one answer per question the respondent actually saw.

- `questions.properties` holds what differs per type (choices, rating steps, contact fields, button text, limits). A JSON column avoids one table per question type.
- `questions.question_type` also covers the welcome screen and ending screens, so every page of a form is one ordered list.
- `answers.value` is JSON because answers are strings, numbers, lists (multi-select) or objects (contact).
- `answers.question_type` is copied at submit time so results stay readable if the question later changes type.
- `responses.status = in_progress` rows are created when someone opens a form; they give the completion rate.
- `forms.submissions_count` is a denormalised counter so the forms list does not count rows per form.

## API overview

All bodies are JSON. Errors use FastAPI's `{"detail": ...}` shape.

Creator (default logged-in creator, see assumptions):

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/forms` | List forms with status and response count |
| POST | `/api/forms` | Create a form (with starter questions) |
| GET / PUT / DELETE | `/api/forms/{id}` | Read, rename or re-theme, delete |
| POST | `/api/forms/{id}/duplicate` | Copy a form and its questions as a draft |
| POST | `/api/forms/{id}/publish` | Publish or unpublish |
| POST | `/api/forms/{id}/questions` | Add a question |
| PUT / DELETE | `/api/forms/{id}/questions/{qid}` | Edit or delete a question |
| PUT | `/api/forms/{id}/questions/reorder` | Save a new order |
| GET | `/api/forms/{id}/responses` | Paginated submissions |
| GET / DELETE | `/api/forms/{id}/responses/{rid}` | One submission in full, or delete it |
| GET | `/api/forms/{id}/stats` | Per-question summaries, completion rate, average time |
| GET | `/api/forms/{id}/export/csv` | Download responses as CSV |
| POST | `/api/upload` | Upload an image or video for a question |

Public (no auth, published forms only):

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/public/forms/{slug}` | The form definition |
| POST | `/api/public/forms/{slug}/start` | Start a session (partial-response tracking) |
| POST | `/api/public/forms/{slug}/validate-step` | Validate one answer and get the next question |
| POST | `/api/public/forms/{slug}/submit` | Validate the whole path and store the response |

## Features

- Builder: add, inline-edit, drag-and-drop reorder and delete questions; short text, long text, multiple choice, dropdown, email, number, yes/no, rating, plus contact info and date; required toggle and description; live preview (desktop and mobile).
- Image or video per page with six desktop layouts (stack, float left/right, split left/right, wallpaper) and two mobile layouts.
- Forms list: status, question and response counts, create, rename, duplicate, publish/unpublish, delete.
- Respondent flow: one question per page with fade-out/fade-in transitions, Enter and arrow keys, A/B/C and Y/N and number shortcuts, progress bar, client and server validation, thank-you screen.
- Results: summary per question, table of submissions, full view of one submission.
- Bonus: branching (logic jumps) with a workflow diagram, custom themes, CSV export, partial-response tracking and completion rate.
- Placeholders ("coming soon"): integrations and webhooks, team collaboration, payments, file-upload questions, scoring, embeds.

## Assumptions and limits

- **No login.** The brief allows a default creator, so every creator endpoint acts as one seeded user (`get_current_user` in `backend/app/database.py`). That one dependency is where real authentication would plug in. Until then, anyone who can reach the API can edit forms and upload files.
- Branching is offered on single-answer questions (yes/no, dropdown, single-select multiple choice) and only jumps forward, so a form cannot loop.
- The phone field is a plain text input (no country picker).
- SQLite allows one writer at a time, so the backend runs as a single process. That is fine for a demo; a busier deployment would move to Postgres by changing `DATABASE_URL`.
- Dark mode and the file-upload question type are not implemented.

## Deployment

Backend on Railway (keeps SQLite and uploads on a volume):

1. New project → Deploy from GitHub repo → set the service **Root Directory** to `backend` (it builds from the `Dockerfile`).
2. Add a **Volume** mounted at `/data`. The image already sets `DATA_DIR=/data`.
3. Set the variable `CORS_ORIGINS` to the frontend URL (for example `https://your-app.vercel.app`).
4. Generate a public domain under Settings → Networking.

Frontend on Vercel:

1. Import the repo and set **Root Directory** to `frontend`.
2. Set `NEXT_PUBLIC_API_URL` to the Railway domain (no trailing slash) and deploy.
