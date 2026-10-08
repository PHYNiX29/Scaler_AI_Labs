# Typeform Clone — Fullstack Platform (Scaler AI Assignment)

A functional, modern Typeform clone replicating Typeform's signature conversational UX, modular form builder, logic branching engine, and respondent analytics.

---

## 🚀 Key Highlights & Architectural Overview

- **Backend**: Python 3.13 + **Flask** (Application Factory, Blueprints, SQLAlchemy ORM, SQLite/PostgreSQL ready).
- **Authentication**: JWT-based creator authentication (`Flask-JWT-Extended`) for form management and stats.
- **Respondent Flow**: Completely **public and frictionless** — zero authentication required for respondents to view and fill published forms.
- **DDoS & Spam Protection**: IP-based rate limiting via `Flask-Limiter` on public endpoints.
- **Dynamic Logic Branching**: Real-time evaluation engine supporting:
  - Yes/No condition branches
  - Multiple Choice single-select option jumps (automatically disables logic jumps when multiple selection is enabled)
  - Custom jump targets or direct jump to the End Page (`thank_you`).
- **Media Orientation Engine**:
  - **Desktop (5 layout orientations)**:
    1. `left_split_1_3`: Left 1/3rd split screen (text content on right)
    2. `right_split_1_3`: Right 1/3rd split screen (text content on left)
    3. `left_box`: Vertically centered square box on the far left
    4. `right_box`: Vertically centered square box on the far right
    5. `background`: Fullscreen ambient background
  - **Mobile (2 layout orientations)**:
    1. `top`: Above text content
    2. `background`: Fullscreen ambient background
- **Welcome Screen Stat Badge**: Exactly one of: `time_to_complete` or `submissions` count.
- **Contact Card Page**: Configurable sub-fields (`first_name`, `last_name`, `phone_number`, `email`, `company`) with per-field required toggles, placeholders, and custom regex validation.
- **Rating Page**: Custom iconography (`star`, `thumbs_up`, `heart`, `number`) and customizable scale (e.g. 0 to 3 or 0 to 5).
- **Typography & Styling**: Per-form and per-question text color, background color, button color, bold, and italic controls.
- **Export & Analytics**: Summary stats (completion rate, average time, choice distributions) and live **CSV export**.
- **Automated Tests**: 100% passing test suite across all flows.
- **Containerized**: Full Docker & Docker Compose setup, with Vercel serverless deployment config.

---

## 🗄️ Database Schema Design

```
+-------------------------------------------------------------+
|                            User                             |
+-------------------------------------------------------------+
| id            : String(36) [PK, UUID]                       |
| email         : String(255) [Unique, Indexed]               |
| password_hash : String(255)                                 |
| name          : String(150)                                 |
| created_at    : DateTime                                    |
| updated_at    : DateTime                                    |
+-------------------------------------------------------------+
                              | 1
                              |
                              | *
+-------------------------------------------------------------+
|                            Form                             |
+-------------------------------------------------------------+
| id                : String(36) [PK, UUID]                   |
| user_id           : String(36) [FK -> User.id]              |
| title             : String(255)                             |
| description       : Text                                    |
| slug              : String(100) [Unique, Indexed]           |
| status            : String(20) ['draft' | 'published']      |
| views_count       : Integer [Default: 0]                    |
| submissions_count : Integer [Default: 0]                    |
| theme_settings    : JSON (colors, font, bold, italic)       |
| settings          : JSON (progress_bar, question_numbers)   |
| created_at        : DateTime                                |
| updated_at        : DateTime                                |
+-------------------------------------------------------------+
             | 1                                     | 1
             |                                       |
             | *                                     | *
+--------------------------------+   +------------------------------------+
|            Question            |   |              Response              |
+--------------------------------+   +------------------------------------+
| id          : String(36) [PK]  |   | id           : String(36) [PK]     |
| form_id     : String(36) [FK]  |   | form_id      : String(36) [FK]     |
| order_index : Integer          |   | session_id   : String(100)         |
| question_type : String(50)     |   | ip_address   : String(45)          |
| title       : String(500)      |   | user_agent   : String(500)         |
| description : Text             |   | status       : String(20)          |
| required    : Boolean          |   | started_at   : DateTime            |
| properties  : JSON             |   | submitted_at : DateTime            |
| media       : JSON (5D / 2M)   |   | time_taken_s : Integer             |
| logic_jumps : JSON             |   +------------------------------------+
| styling     : JSON             |                     | 1
+--------------------------------+                     |
                                                       | *
                                     +------------------------------------+
                                     |               Answer               |
                                     +------------------------------------+
                                     | id            : String(36) [PK]    |
                                     | response_id   : String(36) [FK]    |
                                     | question_id   : String(36) [FK]    |
                                     | question_type : String(50)         |
                                     | value         : JSON (str/list/obj)|
                                     | created_at    : DateTime           |
                                     +------------------------------------+
```

---

## 🛠️ Supported Question Types & Properties

| Type | Description & Specific Capabilities |
|---|---|
| `welcome` | Title, description, button text, **exclusive badge**: `time_to_complete` OR `submissions` count |
| `dropdown` | Title, description, choices list, placeholder, required toggle |
| `multiple_choice` | Choices list, `allow_multiple` (multi-select), `allow_other` ('Other' text input), `allow_none` ('None of the above'), logic branching rules |
| `contact` | Sub-fields: `first_name`, `last_name`, `phone_number`, `email`, `company`. Each can be enabled/disabled, marked required, customized with regex & placeholder |
| `rating` | Icons: `star`, `thumbs_up`, `heart`, `number`. Scale: `max_rating` (3, 5, etc.) |
| `yes_no` | Yes/No selector with independent conditional branching targets for each choice |
| `short_text` | Max character limit, custom placeholder, regex pattern validation |
| `long_text` | Max character limit, multiline input |
| `email` | RFC-compliant email validation |
| `number` | Numeric bounds (`min`, `max`) |
| `thank_you` | End screen with redirect button, reload button toggle, and social links (Twitter, LinkedIn, GitHub, etc.) |

---

## 📡 API Reference Overview

### 1. Authentication (`/api/auth`)
- `POST /api/auth/register`: Register new creator account.
- `POST /api/auth/login`: Creator login, returns JWT access token.
- `GET /api/auth/me`: Get current authenticated user profile (`Bearer <token>`).

### 2. Form Management (`/api/forms`)
- `GET /api/forms`: List creator's forms (with draft/published status and submission counts).
- `POST /api/forms`: Create a new form (includes optional starter template).
- `GET /api/forms/<id>`: Get full form definition with ordered questions.
- `PUT /api/forms/<id>`: Update title, description, theme, or settings.
- `DELETE /api/forms/<id>`: Delete form and all associated questions/responses.
- `POST /api/forms/<id>/duplicate`: Clone form with its entire question set and re-mapped logic jumps.
- `POST /api/forms/<id>/publish`: Toggle form publication status (`published` / `draft`).

### 3. Question Builder (`/api/forms/<id>/questions`)
- `POST /api/forms/<id>/questions`: Add new question of any supported type.
- `PUT /api/forms/<id>/questions/<qid>`: Update question properties, media orientation, logic jumps, or styling.
- `DELETE /api/forms/<id>/questions/<qid>`: Delete question and re-normalize ordering.
- `PUT /api/forms/<id>/questions/reorder`: Reorder questions via array of IDs (drag-and-drop backend).

### 4. Public Respondent Flow (`/api/public`) — *No Auth Required*
- `GET /api/public/forms/<slug>`: Fetch published form for filling; increments view counter.
- `POST /api/public/forms/<slug>/start`: Initialize respondent session (records start time & IP).
- `POST /api/public/forms/<slug>/validate-step`: Real-time validation of step answer + logic jump calculation.
- `POST /api/public/forms/<slug>/submit`: Final submission with server-side validation; updates metrics. *(Rate-limited: 20/min/IP)*.

### 5. Responses & Analytics (`/api/forms/<id>`)
- `GET /api/forms/<id>/responses`: Paginated list of submissions.
- `GET /api/forms/<id>/responses/<rid>`: Detailed view of single submission with answers.
- `DELETE /api/forms/<id>/responses/<rid>`: Delete submission.
- `GET /api/forms/<id>/stats`: Aggregated summary (completion rate, avg time, choice breakdowns).
- `GET /api/forms/<id>/export/csv`: Download CSV export of all submissions.

### 6. Media Uploads
- `POST /api/upload`: Upload image/video file.
- `GET /uploads/<filename>`: Static asset serving.

---

## 🏃 Getting Started Locally

### Prerequisites
- Python 3.11+
- Git

### 1. Setup Virtual Environment
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Run the Development Server
```bash
python run.py
```
The server will start on `http://localhost:5000` and automatically seed the database with sample forms and responses!

### 3. Run Automated Tests
```bash
pytest backend/tests -v
```

---

## 🐳 Running with Docker

```bash
docker-compose up --build
```
Access the backend API at `http://localhost:5000`.

---

## 👥 Seeded Demo Credentials

- **Creator Email**: `demo@scaler.ai`
- **Creator Password**: `scaler2026`
- **Sample Published Forms**:
  - `http://localhost:5000/api/public/forms/customer-feedback` (Customer Experience Survey 2026)
  - `http://localhost:5000/api/public/forms/ai-summit-rsvp` (AI Innovators Summit 2026 RSVP)
