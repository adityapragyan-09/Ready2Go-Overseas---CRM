# Ready2Go CRM

Ready2Go CRM is a production-grade, modular client relationship management system designed specifically for a visa consultancy. This repository follows a highly optimized, clean, and modular architecture designed for high maintainability, low code-duplication, and rapid deployment by a two-developer team.

## Tech Stack
- **Frontend:** React.js (Vite), Tailwind CSS, React Router, Axios
- **Backend:** Python Flask, Flask JWT Extended, SQLAlchemy (PostgreSQL), Flask-CORS, Flask-Migrate
- **Deployment:** Frontend → Vercel, Backend → Render, Database → PostgreSQL (Neon/Supabase)

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

## Database Schema (PostgreSQL)

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

1. **Phase 1: Database Setup & Authentication**
   - Configure PostgreSQL (Neon/Supabase) and run initial database migrations.
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
