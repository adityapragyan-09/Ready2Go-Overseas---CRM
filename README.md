# Ready2Go CRM

Ready2Go CRM is a production-grade, modular client relationship management system designed specifically for a visa consultancy. This repository follows a highly optimized, clean, and modular architecture designed for high maintainability, low code-duplication, and rapid deployment by a two-developer team.

## Tech Stack
- **Frontend:** React.js (Vite), Tailwind CSS, React Router, Axios
- **Backend:** Python Flask, Flask JWT Extended, SQLAlchemy, Flask-CORS, Flask-Migrate
- **Database:** Supabase PostgreSQL
- **Deployment:** Frontend → Vercel, Backend → Render, Database → Supabase

---

## Directory Architecture

The project is structured with a strict separation between the `frontend` and `backend` modules, utilizing a unified applicant management system rather than multiple duplicate CRUD systems:

```text
Ready2Go-CRM/
├── docs/                      # Technical specifications, user manuals, ERDs, etc.
├── frontend/                  # React Single Page Application (SPA) client
│   ├── public/                # Static public files (favicons, manifest.json)
│   └── src/
│       ├── assets/            # Reusable media assets (images, logos, vectors)
│       ├── components/        # Dumb/Reusable UI components
│       │   ├── ui/            # Generic base elements (Button, Input, Dropdown)
│       │   ├── ApplicantTable.jsx
│       │   ├── ApplicantForm.jsx
│       │   ├── SearchBar.jsx
│       │   ├── DocumentUploader.jsx
│       │   ├── StatusTimeline.jsx
│       │   └── ChatBox.jsx
│       ├── config/            # Global API configurations (Axios clients, env constants)
│       ├── context/           # React context providers (AuthContext)
│       ├── hooks/             # Custom hooks (useAuth, useFetch)
│       ├── layouts/           # Page wrapping layout templates (DashboardLayout)
│       ├── pages/             # Page components mapped directly to routes
│       │   ├── Auth/          # Login.jsx
│       │   ├── Dashboard/     # DashboardHome.jsx
│       │   ├── Applicants/    # ApplicantPage.jsx (unified list & details views)
│       │   ├── Employees/     # EmployeeList.jsx
│       │   └── ActivityLogs/  # SystemLogs.jsx (Admin only)
│       ├── routes/            # Route configuration tree and access guards
│       ├── services/          # Direct API request methods mapped to blueprints
│       └── utils/             # Helper validation and formatting routines
└── backend/                   # Flask REST API application
    ├── app/
    │   ├── models/            # SQLAlchemy database models
    │   ├── routes/            # Flask API Blueprints (HTTP controller routes)
    │   ├── services/          # Core business logic / service layer
    │   ├── schemas/           # Marshmallow schema validators & serializers
    │   ├── utils/             # Core backend utility libraries, decorators, validators
    │   ├── config.py          # Centralized configuration (Dev, Test, Prod configs)
    │   ├── extensions.py      # Circular-safe initialization of Flask extensions
    │   └── __init__.py        # Flask app factory initialization
    ├── migrations/            # Flask-Migrate database migration scripts
    └── uploads/               # Local repository filesystem uploads (git-ignored)
```

---

## Architecture Rationale & Best Practices

### Frontend Reusability
- **Reusable Component Composition**: Instead of duplicating tables and forms for each visa type, components like `ApplicantTable` and `ApplicantForm` are completely reusable. They receive parameter inputs (e.g., `visaType`) and render custom fields dynamically.
- **Dynamic Routing**: A single page component `ApplicantPage.jsx` handles applicant workflows. Routes like `/student-visa` and `/tourist-visa` pass a `visaType` prop to this single page, which loads and filters appropriate records.

### Backend Modularity
- **Unified Applicants Controller**: Routes inside `routes/applicants.py` handle queries using request query arguments (e.g. `/api/v1/applicants?visaType=Student`), preventing repetitive CRUD controller routes.
- **Marshmallow Serialization**: The `app/schemas/` directory is added to handle data serialization and validation. It parses incoming JSON payloads and formats outgoing DB models automatically.
- **Service Layer Separation**: Business logic (database writes, status workflows, calculations) is written inside `app/services/` to keep controllers thin and models clean.

---

## Database — Supabase PostgreSQL

We use **Supabase PostgreSQL** as the managed cloud database. SQLAlchemy connects to it via the standard `postgresql://` connection string provided in the Supabase dashboard.

To avoid complex polymorphic table joins or table bloat, we utilize a unified `applicants` table with a **PostgreSQL JSONB** metadata column to store visa-specific attributes.

```text
+------------------------------------+       +------------------------------------+
|               users                |       |             applicants             |
+------------------------------------+       +------------------------------------+
| id (PK)                            |       | id (PK)                            |
| name (VARCHAR)                     |       | name (VARCHAR)                     |
| email (VARCHAR, UNIQUE)            |-------| email (VARCHAR)                    |
| password_hash (VARCHAR)            |       | contact (VARCHAR)                  |
| role (VARCHAR: Admin/Employee)     |       | country (VARCHAR)                  |
| is_active (BOOLEAN)                |       | visa_type (VARCHAR)                |
| created_at (TIMESTAMP)             |       | status (VARCHAR)                   |
+------------------------------------+       | additional_metadata (JSONB)        |
                  |                          | assigned_employee_id (FK -> users) |
                  |                          | created_at (TIMESTAMP)             |
                  |                          | updated_at (TIMESTAMP)             |
                  |                          +------------------------------------+
                  |                                            |
         +--------+---------+-------------------+              |
         |                  |                   |              |
         v                  v                   v              v
+------------------+ +--------------+ +------------------+ +------------------+
|    documents     | |   messages   | |  activity_logs   | |    documents     |
+------------------+ +--------------+ +------------------+ +------------------+
| id (PK)          | | id (PK)      | | id (PK)          | | applicant_id (FK)|
| file_name        | | message      | | action           | +------------------+
| file_path        | | sender_id(FK)| | details          |
| uploaded_by_id   | | created_at   | | user_id (FK)     |
+------------------+ +--------------+ +------------------+
```

### JSONB Metadata Example (`visa_type = Student`)
```json
{
  "university_name": "University of Toronto",
  "course_name": "MS Computer Science",
  "intake_semester": "Fall 2026",
  "ielts_score": 7.5
}
```
*Note: Adding a new visa module requires **zero schema migrations**. Simply add the UI input form fields and map them to keys within `additional_metadata`.*

---

## Supabase Setup

Follow these steps to connect the CRM backend to Supabase PostgreSQL:

### 1. Create a Supabase Project
1. Go to [supabase.com](https://supabase.com) and sign in.
2. Click **New Project**.
3. Choose an organization, enter a project name (e.g., `ready2go-crm`), and set a **strong database password**.
4. Select a region close to your users (e.g., `ap-south-1` for India).
5. Click **Create new project** and wait for provisioning to complete.

### 2. Find Your Database Credentials
1. In your Supabase dashboard, go to **Project Settings** → **Database**.
2. Scroll to the **Connection string** section.
3. Select the **URI** tab.
4. Choose **Transaction Pooler** (port `6543`) — this is recommended for web applications.
5. Your connection string will look like:
   ```
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```

### 3. Configure the Backend
1. Copy `backend/.env.example` to `backend/.env`.
2. Paste your Supabase connection string as the `DATABASE_URL` value.
3. Generate and fill in `SECRET_KEY` and `JWT_SECRET_KEY`.

### 4. Run Migrations
```bash
cd backend
flask db init          # Only on first setup
flask db migrate -m "Initial migration"
flask db upgrade       # Creates tables in Supabase
```

### 5. Verify Tables
Go to **Supabase Dashboard** → **Table Editor** and confirm that the `users` and `activity_logs` tables have been created.

---

## API Blueprint Definitions

All APIs prefix `/api/v1/` and return responses in standard JSON format:

| Method | Endpoint | Query Filters | Description |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/auth/login` | None | User authentication & JWT issuance |
| **GET** | `/api/v1/applicants` | `visaType`, `status`, `search` | Fetch filtered list of applicants |
| **POST** | `/api/v1/applicants` | None | Create a new applicant profile |
| **GET** | `/api/v1/applicants/<id>` | None | Get specific applicant details & metadata |
| **PATCH** | `/api/v1/applicants/<id>` | None | Update applicant details, status, or JSONB |
| **POST** | `/api/v1/applicants/<id>/documents` | None | Upload document file metadata |
| **GET** | `/api/v1/applicants/<id>/messages` | None | Fetch chat history |
| **POST** | `/api/v1/applicants/<id>/messages` | None | Send a chat message |
| **GET** | `/api/v1/employees` | None | List employees (Admin only) |
| **GET** | `/api/v1/activity-logs` | `user_id` | Audit trail of logs (Admin only) |

---

## Deployment

### Backend → Render

1. Create a new **Web Service** on [render.com](https://render.com).
2. Connect the GitHub repository.
3. Set the **Root Directory** to `backend`.
4. Set the **Build Command** to `pip install -r requirements.txt`.
5. Set the **Start Command** to `gunicorn run:app`.
6. Add the following **Environment Variables**:

| Variable | Value | Required |
|:---------|:------|:--------:|
| `FLASK_ENV` | `production` | ✅ |
| `SECRET_KEY` | *(generate: `python -c "import secrets; print(secrets.token_hex(32))"`)* | ✅ |
| `JWT_SECRET_KEY` | *(generate a different key)* | ✅ |
| `DATABASE_URL` | *(Supabase Transaction Pooler URI)* | ✅ |
| `UPLOAD_FOLDER` | `uploads/` | ✅ |
| `FRONTEND_URL` | `https://your-app.vercel.app` | ✅ |
| `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` | `60` | ❌ |

### Frontend → Vercel

1. Create a new project on [vercel.com](https://vercel.com).
2. Connect the GitHub repository.
3. Set the **Root Directory** to `frontend`.
4. Vercel auto-detects Vite. Deploy.

---

## Supabase Connection Checklist

Use this checklist when setting up the database for the first time:

- [ ] Create a new Supabase project
- [ ] Save the database password securely
- [ ] Copy the **Transaction Pooler** connection string (port 6543)
- [ ] Paste it as `DATABASE_URL` in `backend/.env`
- [ ] Test the connection: `python -c "from app import create_app; app = create_app(); print('OK')"`
- [ ] Run migrations: `flask db init && flask db migrate -m "Initial" && flask db upgrade`
- [ ] Verify tables in Supabase Dashboard → Table Editor
- [ ] Create the first Admin user via Flask shell or seed script

---

## First-Time Developer Setup Guide

```bash
# 1. Clone the repository
git clone https://github.com/adityapragyan-09/Ready2Go-Overseas---CRM.git
cd Ready2Go-Overseas---CRM

# 2. Set up the backend
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env:
#   - Paste your Supabase DATABASE_URL
#   - Generate and paste SECRET_KEY
#   - Generate and paste JWT_SECRET_KEY

# 4. Run database migrations
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 5. Start the backend server
python run.py
# Server runs at http://localhost:5000

# 6. (In a new terminal) Set up the frontend
cd ../frontend
npm install
npm run dev
# Frontend runs at http://localhost:5173
```

---

## Git Workflow Strategy (GitHub Flow)

For a two-member team, a lean and clean workflow keeps speed high while maintaining control:

1. **`main`**: Reflects stable production. Keep protected; direct commits are prohibited.
2. **`feature/<name>`** (e.g., `feature/applicant-upload`): Short-lived branch for individual tasks.
3. **Collaboration Protocol**:
   - Developer A commits code on their `feature/*` branch and creates a Pull Request (PR) targeting `main`.
   - Developer B reviews and approves the PR.
   - PR is merged into `main`, which automatically triggers a staging/production build on Render and Vercel.

---

## Development Roadmap (Recommended Order)

1. **Phase 1: Database Setup & Authentication** ✅
   - Configure Supabase PostgreSQL and run initial database migrations.
   - Build JWT credentials routes in Flask and design route guards on the frontend.
2. **Phase 2: Core Applicant Module**
   - Implement the `applicants` SQLAlchemy models and routes.
   - Create unified `ApplicantTable` and `ApplicantForm` on the React app.
3. **Phase 3: Visa Parameter Integration**
   - Bind the sidebar visa pages to use the single parameterized `<ApplicantPage visaType="..." />` component.
4. **Phase 4: Document Storage & Chats**
   - Connect uploading API handlers and design the `ChatBox` and `DocumentUploader` wrappers.
5. **Phase 5: Dashboards & Logging**
   - Add metrics compilation on the backend and implement activity logging. Design the admin panels and dashboard KPIs on the frontend.
