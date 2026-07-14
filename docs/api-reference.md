# Ready2Go CRM API Reference

Base URL: `http://localhost:8000` (development)  
API Prefix: `/api/v1`  

**Version:** 1.0.0  
**Application:** Ready2Go CRM  
**Company:** Ready2Go Overseas

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Standard Response Envelope](#2-standard-response-envelope)
3. [Error Codes](#3-error-codes)
4. [Rate Limiting](#4-rate-limiting)
5. [Endpoints](#5-endpoints)
   - [5.1 Auth](#51-auth)
   - [5.2 Employees](#52-employees)
   - [5.3 Applicants](#53-applicants)
   - [5.4 Documents](#54-documents)
   - [5.5 Progress](#55-progress)
   - [5.6 Chat](#56-chat)
   - [5.7 Notifications](#57-notifications)
   - [5.8 Dashboard](#58-dashboard)
   - [5.9 Activity Logs](#59-activity-logs)
   - [5.10 Infrastructure](#510-infrastructure)
6. [Pagination](#6-pagination)
7. [Filters and Search](#7-filters-and-search)
8. [File Uploads](#8-file-uploads)
9. [Role-Based Access Control](#9-role-based-access-control-rbac)
10. [Common Request/Response Examples](#10-common-requestresponse-examples)

---

## 1. Authentication

### 1.1 Method

The API uses **JWT (JSON Web Token)** Bearer token authentication. All authenticated endpoints require the `Authorization` header:

```
Authorization: Bearer <token>
```

### 1.2 Obtaining a Token

Send a `POST /api/v1/auth/login` request with valid credentials. The response includes a `token` field containing the JWT access token.

### 1.3 Token Claims

Decoded JWT payload:

```json
{
  "sub": "1",
  "role": "admin",
  "name": "Admin User",
  "iat": 1700000000,
  "exp": 1700003600,
  "iss": "Ready2Go CRM",
  "aud": "Ready2Go CRM",
  "type": "access",
  "jti": "1_1700000000"
}
```

| Claim | Description |
|-------|-------------|
| `sub` | User ID (primary key) |
| `role` | User role (`admin` or `employee`) |
| `name` | User display name |
| `iat` | Issued-at timestamp (UTC Unix) |
| `exp` | Expiration timestamp (UTC Unix) |
| `iss` | Issuer — always `"Ready2Go CRM"` |
| `aud` | Audience — always `"Ready2Go CRM"` |
| `type` | Token type — always `"access"` |
| `jti` | Unique token identifier |

### 1.4 Token Expiration

Tokens expire after **60 minutes** by default (configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`). When a token expires, the API returns `401 Unauthorized` with error code `UNAUTHORIZED`. The client must obtain a fresh token by logging in again.

### 1.5 Token Validation

All protected endpoints validate:
- Signature integrity (HMAC-SHA256 via `HS256` algorithm)
- Expiration time
- Token `type = "access"`
- Presence of `sub` and `exp` claims

### 1.6 OAuth2 Flow

The API uses `OAuth2PasswordBearer` with `tokenUrl="/api/v1/auth/login"`. The standard `Authorization` header mechanism applies.

---

## 2. Standard Response Envelope

Every API endpoint returns a consistent JSON envelope:

```json
{
  "success": true,
  "message": "Human-readable description",
  "data": { ... },
  "error": null,
  "errors": null,
  "timestamp": "2026-07-14T10:30:00.000000+00:00",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### 2.1 Success Response

```json
{
  "success": true,
  "message": "Applicant created successfully.",
  "data": { ... },
  "error": null,
  "errors": null,
  "timestamp": "2026-07-14T10:30:00.000000+00:00",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### 2.2 Error Response

```json
{
  "success": false,
  "message": "Invalid email or password.",
  "data": null,
  "error": "UNAUTHORIZED",
  "errors": null,
  "timestamp": "2026-07-14T10:30:00.000000+00:00",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### 2.3 Validation Error Response

```json
{
  "success": false,
  "message": "Validation failed.",
  "data": null,
  "error": "VALIDATION_ERROR",
  "errors": {
    "email": ["value is not a valid email address"],
    "password": ["String should have at least 6 characters"]
  },
  "timestamp": "2026-07-14T10:30:00.000000+00:00",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### 2.4 Envelope Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | `true` for successful requests, `false` for errors |
| `message` | `string` | Human-readable description of the result |
| `data` | `object` or `array` or `null` | Response payload (present on success only) |
| `error` | `string` or `null` | Machine-readable error code (present on failure only) |
| `errors` | `object` or `null` | Field-level validation errors (present on validation failure) |
| `timestamp` | `string` (ISO-8601) | UTC timestamp of the response |
| `request_id` | `string` (UUID) or `null` | Unique request identifier for tracing |

Every response includes an `X-Request-ID` HTTP header matching the `request_id` field.

---

## 3. Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| `400 Bad Request` | — | Invalid input, invalid transition, duplicate email, etc. |
| `401 Unauthorized` | `UNAUTHORIZED` | Missing, expired, or invalid JWT token |
| `403 Forbidden` | `FORBIDDEN` | Authenticated but insufficient permissions |
| `404 Not Found` | `NOT_FOUND` | Resource does not exist or has been soft-deleted |
| `422 Unprocessable Entity` | `VALIDATION_ERROR` | Request body failed Pydantic validation |
| `429 Too Many Requests` | `RATE_LIMITED` | Rate limit exceeded |
| `500 Internal Server Error` | `INTERNAL_ERROR` | Unhandled server-side error |

### Detailed Error Scenarios

| Scenario | Status | Error Field | Message Example |
|----------|--------|-------------|-----------------|
| Invalid credentials | `401` | `error`: `"UNAUTHORIZED"` | `"Invalid email or password."` |
| Account deactivated | `403` | — | `"Account has been deactivated."` |
| Non-admin on admin route | `403` | — | `"Admin access required."` |
| Soft-deleted resource | `404` | — | `"Applicant not found."` |
| Status transition violation | `400` | — | `"Invalid workflow transition: Cannot move state from 'Inquiry' to 'Visa Approved'."` |
| Duplicate email | `400` | — | `"An employee account with this email address already exists."` |
| Invalid visa_type | `400` | — | `"Invalid visa_type 'invalid'. Allowed: student, visit, tourist, business"` |
| Self-deactivation | `400` | — | `"Self-deactivation is prohibited."` |
| Rate limited | `429` | `error`: `"RATE_LIMITED"` | `"Too many requests. Please slow down."` |
| Internal error | `500` | `error`: `"INTERNAL_ERROR"` | `"Internal server error."` |

---

## 4. Rate Limiting

An in-memory IP-based rate limiter is active on all routes except `/health`.

| Parameter | Default |
|-----------|---------|
| Requests per minute | 600 |
| Window | 60 seconds sliding |

When rate-limited, the response includes:
- HTTP `429 Too Many Requests` status
- `Retry-After` header with seconds to wait
- Response body with `error: "RATE_LIMITED"` and `retry_after_seconds` field

> **Note:** The in-memory rate limiter is not suitable for multi-process production deployments behind a load balancer. Use a centralized store (Redis) or an API gateway in production.

---

## 5. Endpoints

### 5.1 Auth

Base: `POST /api/v1/auth/login` (token URL for OAuth2 flow)

#### `POST /api/v1/auth/login`

Authenticate with email and password. Returns a JWT token and user profile.

**Request Body:**

```json
{
  "email": "admin@ready2go.com",
  "password": "securepassword"
}
```

**Response `201 Created`:**

```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": 1,
      "name": "Admin User",
      "email": "admin@ready2go.com",
      "phone": "+1234567890",
      "role": "admin",
      "is_active": true,
      "created_at": "2026-01-01T00:00:00+00:00",
      "updated_at": "2026-07-14T10:30:00+00:00"
    }
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**Error `401 Unauthorized`:**

```json
{
  "success": false,
  "message": "Invalid email or password.",
  "data": null,
  "error": "UNAUTHORIZED",
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@ready2go.com", "password": "securepassword"}'
```

---

#### `GET /api/v1/auth/me`

Return the profile of the currently authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Response:**

```json
{
  "success": true,
  "message": "User profile retrieved.",
  "data": {
    "id": 1,
    "name": "Admin User",
    "email": "admin@ready2go.com",
    "phone": "+1234567890",
    "role": "admin",
    "is_active": true,
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-07-14T10:30:00+00:00"
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
```

---

#### `POST /api/v1/auth/logout`

Record the logout event in activity logs. The JWT itself is stateless; the frontend should discard it on the client side.

**Headers:** `Authorization: Bearer <token>`

**Response:**

```json
{
  "success": true,
  "message": "Logout recorded successfully.",
  "data": null,
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <token>"
```

---

### 5.2 Employees

Base: `/api/v1/employees`

#### `GET /api/v1/employees` (Admin)

List all employees with optional search, filters, and pagination.

**Access:** Admin only

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search` | `string` | — | Global search (name, email, employee_code, department) |
| `role` | `string` | — | Filter by role (`admin`, `employee`) |
| `department` | `string` | — | Filter by department (partial match) |
| `is_active` | `boolean` | — | Filter by active/inactive status |
| `page` | `integer` | `1` | Page number (1-indexed) |
| `page_size` | `integer` | `10` | Items per page |

**Response:**

```json
{
  "success": true,
  "message": "Employees retrieved successfully.",
  "data": {
    "total_count": 5,
    "page": 1,
    "page_size": 10,
    "items": [
      {
        "id": 1,
        "employee_code": "EMP-000001",
        "full_name": "Admin User",
        "email": "admin@ready2go.com",
        "phone": "+1234567890",
        "role": "admin",
        "designation": "Operations Manager",
        "department": "Management",
        "profile_photo": null,
        "is_active": true,
        "last_login": "2026-07-14T08:00:00+00:00",
        "last_logout": "2026-07-14T09:00:00+00:00",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-07-14T08:00:00+00:00",
        "created_by": null
      }
    ]
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl "http://localhost:8000/api/v1/employees?search=admin&role=admin&page=1&page_size=10" \
  -H "Authorization: Bearer <token>"
```

---

#### `POST /api/v1/employees` (Admin)

Register a new system user with an auto-generated employee code.

**Access:** Admin only

**Request Body:**

```json
{
  "full_name": "Jane Counsellor",
  "email": "jane@ready2go.com",
  "phone": "+919876543210",
  "password": "temp123456",
  "role": "employee",
  "designation": "Visa Counsellor",
  "department": "Visa Processing",
  "profile_photo": null
}
```

**Response `201 Created`:**

```json
{
  "success": true,
  "message": "Employee account registered successfully.",
  "data": {
    "id": 6,
    "employee_code": "EMP-000006",
    "full_name": "Jane Counsellor",
    "email": "jane@ready2go.com",
    "phone": "+919876543210",
    "role": "employee",
    "designation": "Visa Counsellor",
    "department": "Visa Processing",
    "profile_photo": null,
    "is_active": true,
    "last_login": null,
    "last_logout": null,
    "created_at": "2026-07-14T10:30:00+00:00",
    "updated_at": "2026-07-14T10:30:00+00:00",
    "created_by": 1
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/v1/employees \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Jane Counsellor",
    "email": "jane@ready2go.com",
    "phone": "+919876543210",
    "password": "temp123456",
    "role": "employee",
    "designation": "Visa Counsellor",
    "department": "Visa Processing"
  }'
```

---

#### `GET /api/v1/employees/{id}` (Admin)

Retrieve a single employee by ID.

**Access:** Admin only

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/employees/1 \
  -H "Authorization: Bearer <token>"
```

---

#### `PUT /api/v1/employees/{id}` (Admin)

Update an employee record.

**Access:** Admin only

**Request Body:**

```json
{
  "full_name": "Admin Updated",
  "phone": "+1234567899",
  "role": "admin",
  "designation": "Senior Manager",
  "department": "Management",
  "profile_photo": null
}
```

**cURL Example:**

```bash
curl -X PUT http://localhost:8000/api/v1/employees/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Admin Updated", "designation": "Senior Manager"}'
```

---

#### `PATCH /api/v1/employees/{id}/status` (Admin)

Toggle employee active/inactive status. Self-deactivation is prohibited.

**Access:** Admin only

**Request Body:**

```json
{
  "is_active": false
}
```

**cURL Example:**

```bash
curl -X PATCH http://localhost:8000/api/v1/employees/6/status \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

---

#### `PATCH /api/v1/employees/{id}/reset-password` (Admin)

Reset an employee's password.

**Access:** Admin only

**Request Body:**

```json
{
  "password": "newSecurePass123"
}
```

**cURL Example:**

```bash
curl -X PATCH http://localhost:8000/api/v1/employees/6/reset-password \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"password": "newSecurePass123"}'
```

---

#### `GET /api/v1/employees/profile/me`

Retrieve the authenticated user's own profile. Accessible to all authenticated employees and admins.

**Access:** Authenticated

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/employees/profile/me \
  -H "Authorization: Bearer <token>"
```

---

#### `PUT /api/v1/employees/profile/me`

Update own profile fields (Phone, Photo, Designation, Department). Accessible to all authenticated employees and admins.

**Access:** Authenticated

**Request Body:**

```json
{
  "phone": "+919876543210",
  "designation": "Senior Visa Counsellor",
  "department": "Operations"
}
```

**cURL Example:**

```bash
curl -X PUT http://localhost:8000/api/v1/employees/profile/me \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210", "designation": "Senior Visa Counsellor"}'
```

---

### 5.3 Applicants

Base: `/api/v1/applicants`

All endpoints require a valid JWT token.

#### `POST /api/v1/applicants`

Create a new applicant record. Auto-generates an applicant code (`APP-000001` format), seeds initial progress history, and creates a system chat message.

**Access:** Authenticated

**Request Body:**

```json
{
  "full_name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+919876543210",
  "country": "India",
  "visa_type": "student",
  "status": "inquiry",
  "metadata": {
    "university": "University of Toronto",
    "course": "MSc Computer Science",
    "intake": "Fall 2026"
  },
  "notes": "Initial inquiry from college fair.",
  "assigned_to": 2
}
```

**Response `201 Created`:**

```json
{
  "success": true,
  "message": "Applicant created successfully.",
  "data": {
    "id": 42,
    "applicant_code": "APP-000042",
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+919876543210",
    "country": "India",
    "visa_type": "student",
    "status": "inquiry",
    "metadata": {
      "university": "University of Toronto",
      "course": "MSc Computer Science",
      "intake": "Fall 2026"
    },
    "notes": "Initial inquiry from college fair.",
    "assigned_to": 2,
    "created_by": 1,
    "created_by_name": "Admin User",
    "created_at": "2026-07-14T10:30:00+00:00",
    "updated_at": "2026-07-14T10:30:00+00:00"
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/v1/applicants \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+919876543210",
    "country": "India",
    "visa_type": "student",
    "status": "inquiry"
  }'
```

---

#### `GET /api/v1/applicants`

List applicants with optional filters, search, and pagination.

**Access:** Authenticated

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `visa_type` | `string` | — | Filter by visa type (`student`, `visit`, `tourist`, `business`) |
| `status` | `string` | — | Filter by application status (see status list) |
| `country` | `string` | — | Filter by country (partial match) |
| `assigned_to` | `integer` | — | Filter by assigned employee ID |
| `search` | `string` | — | Search across name, email, phone, applicant_code |
| `page` | `integer` | `1` | Page number (1-indexed) |
| `page_size` | `integer` | `20` | Items per page (max 100) |

**Response:**

```json
{
  "success": true,
  "message": "Applicants retrieved successfully.",
  "data": {
    "applicants": [
      {
        "id": 42,
        "applicant_code": "APP-000042",
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+919876543210",
        "country": "India",
        "visa_type": "student",
        "status": "inquiry",
        "metadata": null,
        "notes": null,
        "assigned_to": 2,
        "created_by": 1,
        "created_by_name": "Admin User",
        "created_at": "2026-07-14T10:30:00+00:00",
        "updated_at": "2026-07-14T10:30:00+00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl "http://localhost:8000/api/v1/applicants?visa_type=student&status=inquiry&search=john&page=1&page_size=20" \
  -H "Authorization: Bearer <token>"
```

---

#### `GET /api/v1/applicants/{id}`

Retrieve a single applicant by ID.

**Access:** Authenticated

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/applicants/42 \
  -H "Authorization: Bearer <token>"
```

---

#### `PUT /api/v1/applicants/{id}`

Update an existing applicant record. Only fields included in the request body will be updated.

**Access:** Authenticated

**Request Body:**

```json
{
  "full_name": "John Doe Updated",
  "phone": "+919876543211",
  "status": "documents_pending",
  "notes": "Requested passport and academic documents.",
  "assigned_to": 3
}
```

**cURL Example:**

```bash
curl -X PUT http://localhost:8000/api/v1/applicants/42 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe Updated",
    "status": "documents_pending",
    "notes": "Requested passport and academic documents.",
    "assigned_to": 3
  }'
```

---

#### `DELETE /api/v1/applicants/{id}`

Soft-delete an applicant. Sets `is_deleted = True` and records the deletion timestamp and deleter ID. The row remains in the database.

**Access:** Authenticated

**Response:**

```json
{
  "success": true,
  "message": "Applicant 'John Doe Updated' deleted successfully.",
  "data": null,
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl -X DELETE http://localhost:8000/api/v1/applicants/42 \
  -H "Authorization: Bearer <token>"
```

---

### 5.4 Documents

Base: `/api/v1/documents`

#### `POST /api/v1/documents/upload`

Upload a document file for an applicant. Validates file extension, size, document type, and applicant existence.

**Access:** Authenticated

**Request:** Multipart form data

| Field | Type | Description |
|-------|------|-------------|
| `file` | `file` | The file to upload (PDF, JPG, JPEG, PNG, DOC, DOCX) |
| `applicant_id` | `integer` | Applicant ID to associate the document with |
| `document_type` | `string` | Document type from the allowed list |

**Allowed File Extensions:** `.pdf`, `.jpg`, `.jpeg`, `.png`, `.doc`, `.docx`  
**Maximum File Size:** 500 MB  
**Allowed Document Types:** `passport`, `national_id`, `photograph`, `academic_certificate`, `ielts`, `toefl`, `offer_letter`, `bank_statement`, `financial_proof`, `visa_application`, `insurance`, `employment_proof`, `travel_itinerary`, `other`

**Response `201 Created`:**

```json
{
  "success": true,
  "message": "Document uploaded successfully.",
  "data": {
    "id": 15,
    "document_code": "DOC-000015",
    "applicant_id": 42,
    "document_type": "passport",
    "original_file_name": "passport_scan.pdf",
    "stored_file_name": "a1b2c3d4e5f6.pdf",
    "storage_path": "applicants/APP-000042/a1b2c3d4e5f6.pdf",
    "mime_type": "application/pdf",
    "file_extension": "pdf",
    "file_size": 245760,
    "uploaded_by": 1,
    "uploaded_at": "2026-07-14T10:30:00+00:00",
    "is_deleted": false
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/passport_scan.pdf" \
  -F "applicant_id=42" \
  -F "document_type=passport"
```

---

#### `GET /api/v1/documents/applicant/{id}`

List all active (non-deleted) documents for a specific applicant.

**Access:** Authenticated

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/documents/applicant/42 \
  -H "Authorization: Bearer <token>"
```

---

#### `GET /api/v1/documents/{id}/download`

Generate a secure, temporary signed download URL for a document. The URL expires after a configurable timeout (default: 60 minutes).

**Access:** Authenticated

**Response:**

```json
{
  "success": true,
  "message": "Document download URL generated successfully.",
  "data": {
    "document_code": "DOC-000015",
    "original_file_name": "passport_scan.pdf",
    "download_url": "https://supabase.co/storage/v1/object/signed/..."
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/documents/15/download \
  -H "Authorization: Bearer <token>"
```

---

#### `GET /api/v1/documents/{id}/view`

Generate a secure, temporary signed view URL for a document. The URL expires after a configurable timeout (default: 60 minutes).

**Access:** Authenticated

**Response:**

```json
{
  "success": true,
  "message": "Document view URL generated successfully.",
  "data": {
    "document_code": "DOC-000015",
    "original_file_name": "passport_scan.pdf",
    "view_url": "https://supabase.co/storage/v1/object/signed/..."
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/documents/15/view \
  -H "Authorization: Bearer <token>"
```

---

#### `DELETE /api/v1/documents/{id}`

Soft-delete a document record. The underlying storage asset is retained for recovery.

**Access:** Authenticated

**Response:**

```json
{
  "success": true,
  "message": "Document 'passport_scan.pdf' deleted successfully.",
  "data": null,
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl -X DELETE http://localhost:8000/api/v1/documents/15 \
  -H "Authorization: Bearer <token>"
```

---

### 5.5 Progress

Base: `/api/v1/progress`

#### `GET /api/v1/progress/applicant/{id}`

Retrieve the complete history timeline of status changes and notes for an applicant. Ordered chronologically ascending.

**Access:** Authenticated

**Response:**

```json
{
  "success": true,
  "message": "Applicant progress history retrieved successfully.",
  "data": [
    {
      "id": 1,
      "applicant_id": 42,
      "previous_status": null,
      "current_status": "inquiry",
      "remarks": "Applicant file profile registered and pipeline initiated.",
      "updated_by": 1,
      "updated_at": "2026-07-14T10:30:00+00:00",
      "is_system_generated": true,
      "updated_by_name": "System"
    },
    {
      "id": 2,
      "applicant_id": 42,
      "previous_status": "inquiry",
      "current_status": "documents_pending",
      "remarks": "Requested passport and academic documents.",
      "updated_by": 2,
      "updated_at": "2026-07-14T11:00:00+00:00",
      "is_system_generated": false,
      "updated_by_name": "Jane Counsellor"
    }
  ],
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/progress/applicant/42 \
  -H "Authorization: Bearer <token>"
```

---

#### `PUT /api/v1/progress/applicant/{id}`

Update an applicant's status. Validates against a strict state transition matrix. Cannot transition to the current status.

**Access:** Authenticated

**Valid State Transitions:**

```
inquiry              -> documents_pending, cancelled
documents_pending    -> documents_submitted, cancelled
documents_submitted  -> application_processing, cancelled
application_processing -> interview_scheduled, visa_approved, visa_rejected, cancelled
interview_scheduled  -> visa_approved, visa_rejected, cancelled
visa_approved        -> completed, cancelled
completed            -> (terminal)
visa_rejected        -> (terminal)
cancelled            -> (terminal)
```

**Request Body:**

```json
{
  "status": "documents_pending",
  "remarks": "Requested passport and academic transcripts from applicant."
}
```

**Response:**

```json
{
  "success": true,
  "message": "Applicant status updated successfully.",
  "data": {
    "id": 2,
    "applicant_id": 42,
    "previous_status": "inquiry",
    "current_status": "documents_pending",
    "remarks": "Requested passport and academic transcripts from applicant.",
    "updated_by": 2,
    "updated_at": "2026-07-14T11:00:00+00:00",
    "is_system_generated": false,
    "updated_by_name": "Jane Counsellor"
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl -X PUT http://localhost:8000/api/v1/progress/applicant/42 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "documents_pending", "remarks": "Requested passport and academic transcripts from applicant."}'
```

---

#### `POST /api/v1/progress/note`

Add a progress comment/note without changing the applicant's status. The note is linked to the current status.

**Access:** Authenticated

**Request Body:**

```json
{
  "applicant_id": 42,
  "remarks": "Followed up with applicant — will submit documents by Friday."
}
```

**Response `201 Created`:**

```json
{
  "success": true,
  "message": "Progress note appended successfully.",
  "data": {
    "id": 3,
    "applicant_id": 42,
    "previous_status": "documents_pending",
    "current_status": "documents_pending",
    "remarks": "Followed up with applicant — will submit documents by Friday.",
    "updated_by": 2,
    "updated_at": "2026-07-14T12:00:00+00:00",
    "is_system_generated": false,
    "updated_by_name": "Jane Counsellor"
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/v1/progress/note \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"applicant_id": 42, "remarks": "Followed up with applicant — will submit documents by Friday."}'
```

---

#### `GET /api/v1/progress/latest/{id}`

Retrieve the most recent progress history entry for an applicant.

**Access:** Authenticated

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/progress/latest/42 \
  -H "Authorization: Bearer <token>"
```

---

### 5.6 Chat

Base: `/api/v1/chat`

#### `GET /api/v1/chat/applicant/{id}`

Retrieve the complete chronological conversation thread for an applicant. Ordered oldest to newest (`created_at ASC`).

**Access:** Authenticated

**Response:**

```json
{
  "success": true,
  "message": "Conversation retrieved successfully.",
  "data": [
    {
      "id": 1,
      "applicant_id": 42,
      "sender_id": 1,
      "message": "Applicant record registered under code APP-000042.",
      "message_type": "system",
      "attachment_url": null,
      "is_system_message": true,
      "created_at": "2026-07-14T10:30:00+00:00",
      "updated_at": "2026-07-14T10:30:00+00:00",
      "sender_name": "System"
    },
    {
      "id": 2,
      "applicant_id": 42,
      "sender_id": 2,
      "message": "Hello John, welcome to Ready2Go Overseas! Please share your passport copy.",
      "message_type": "text",
      "attachment_url": null,
      "is_system_message": false,
      "created_at": "2026-07-14T11:00:00+00:00",
      "updated_at": "2026-07-14T11:00:00+00:00",
      "sender_name": "Jane Counsellor"
    }
  ],
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/chat/applicant/42 \
  -H "Authorization: Bearer <token>"
```

---

#### `POST /api/v1/chat/applicant/{id}`

Post a new chat message inside the applicant collaboration thread. Only authenticated employees/admins with active accounts can post messages.

**Access:** Authenticated

**Request Body:**

```json
{
  "content": "Please upload your IELTS test report form at your earliest convenience.",
  "message_type": "text",
  "attachment_url": null
}
```

**Response `201 Created`:**

```json
{
  "success": true,
  "message": "Message sent successfully.",
  "data": {
    "id": 3,
    "applicant_id": 42,
    "sender_id": 2,
    "message": "Please upload your IELTS test report form at your earliest convenience.",
    "message_type": "text",
    "attachment_url": null,
    "is_system_message": false,
    "created_at": "2026-07-14T12:00:00+00:00",
    "updated_at": "2026-07-14T12:00:00+00:00",
    "sender_name": "Jane Counsellor"
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/v1/chat/applicant/42 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "Please upload your IELTS test report form.", "message_type": "text"}'
```

---

#### `DELETE /api/v1/chat/{message_id}`

Soft-delete a chat message. Users can only delete their own messages, unless they hold the `admin` role.

**Access:** Authenticated (owner or admin)

**Response:**

```json
{
  "success": true,
  "message": "Message deleted successfully.",
  "data": {
    "id": 3,
    "applicant_id": 42,
    "sender_id": 2,
    "message": "Please upload your IELTS test report form at your earliest convenience.",
    "message_type": "text",
    "attachment_url": null,
    "is_system_message": false,
    "created_at": "2026-07-14T12:00:00+00:00",
    "updated_at": "2026-07-14T12:05:00+00:00",
    "sender_name": "Jane Counsellor"
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl -X DELETE http://localhost:8000/api/v1/chat/3 \
  -H "Authorization: Bearer <token>"
```

---

#### `GET /api/v1/chat/latest/{id}`

Retrieve the most recent message in an applicant's chat thread.

**Access:** Authenticated

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/chat/latest/42 \
  -H "Authorization: Bearer <token>"
```

---

### 5.7 Notifications

Base: `/api/v1/notifications`

#### `GET /api/v1/notifications/unread-count`

Get the count of unread notifications visible to the authenticated user.

**Access:** Authenticated

**Response:**

```json
{
  "success": true,
  "message": "Unread notification count retrieved successfully.",
  "data": {
    "unread_count": 3
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/notifications/unread-count \
  -H "Authorization: Bearer <token>"
```

---

#### `GET /api/v1/notifications`

Retrieve paginated notifications visible to the authenticated user.

**Access:** Authenticated

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | `integer` | `1` | Page number (1-indexed) |
| `page_size` | `integer` | `10` | Items per page |

**Visibility Rules:**
- **Admins:** See their own targeted notifications plus system-wide notifications (those with no specific recipient).
- **Employees:** See only their own targeted notifications.

**Response:**

```json
{
  "success": true,
  "message": "Notifications retrieved successfully.",
  "data": {
    "total_count": 10,
    "page": 1,
    "page_size": 10,
    "items": [
      {
        "id": 5,
        "notification_code": "NOT-000005",
        "title": "New Applicant Registered",
        "message": "Applicant 'John Doe' (APP-000042) has been registered.",
        "type": "success",
        "module": "applicant",
        "priority": "medium",
        "recipient_user_id": 1,
        "created_by": 1,
        "reference_type": "applicant",
        "reference_id": 42,
        "is_read": false,
        "read_at": null,
        "created_at": "2026-07-14T10:30:00+00:00"
      }
    ]
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl "http://localhost:8000/api/v1/notifications?page=1&page_size=10" \
  -H "Authorization: Bearer <token>"
```

---

#### `PATCH /api/v1/notifications/{id}/read`

Mark a specific notification as read.

**Access:** Authenticated

**Authorization:** Employees can only mark their own notifications as read. Admins can also mark system-wide notifications as read.

**cURL Example:**

```bash
curl -X PATCH http://localhost:8000/api/v1/notifications/5/read \
  -H "Authorization: Bearer <token>"
```

---

#### `PATCH /api/v1/notifications/read-all`

Mark all unread notifications visible to the user as read.

**Access:** Authenticated

**Response:**

```json
{
  "success": true,
  "message": "Successfully marked 3 notifications as read.",
  "data": {
    "updated_count": 3
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl -X PATCH http://localhost:8000/api/v1/notifications/read-all \
  -H "Authorization: Bearer <token>"
```

---

#### `DELETE /api/v1/notifications/{id}`

Delete a specific notification from the database.

**Access:** Authenticated

**Authorization:** Same visibility rules as marking read.

**cURL Example:**

```bash
curl -X DELETE http://localhost:8000/api/v1/notifications/5 \
  -H "Authorization: Bearer <token>"
```

---

### 5.8 Dashboard

Base: `/api/v1/dashboard`

#### `GET /api/v1/dashboard/summary`

Retrieve high-level overview metrics / count cards.

**Access:** Authenticated

**Response:**

```json
{
  "success": true,
  "message": "Dashboard summary retrieved successfully.",
  "data": {
    "total_applicants": 150,
    "student_visa": 85,
    "visit_visa": 30,
    "tourist_visa": 25,
    "business_visa": 10,
    "applications_processing": 40,
    "documents_pending": 25,
    "documents_uploaded": 320,
    "visa_approved": 35,
    "visa_rejected": 8,
    "completed_applications": 50,
    "total_employees": 12,
    "active_employees": 10,
    "inactive_employees": 2,
    "todays_logins": 5,
    "unread_notifications": 3
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/dashboard/summary \
  -H "Authorization: Bearer <token>"
```

---

#### `GET /api/v1/dashboard/charts`

Retrieve detailed metrics and datasets for visualizations and trends.

**Access:** Authenticated

**Scoping:** Counselors see metrics scoped to their assigned applicants only. Admins see global metrics.

**Response contains:**
- `applicant_analytics`: by_country, by_visa_type, by_status, monthly_registrations, yearly_registrations
- `document_analytics`: documents_uploaded, pending_documents, by_type, storage_usage, largest_documents
- `progress_analytics`: status_distribution, average_completion_time (days), current_pipeline
- `chat_analytics`: messages_today, system_messages, employee_messages
- `notification_analytics`: unread_notifications, notifications_today, notifications_by_module

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/dashboard/charts \
  -H "Authorization: Bearer <token>"
```

---

#### `GET /api/v1/dashboard/recent`

Retrieve recent activity feed across the CRM — latest 5 items per category.

**Access:** Authenticated

**Scoping:** Counselors see activity scoped to their assigned applicants. Admins see global activity.

**Response contains:**
- `recent_applicants`, `recent_documents`, `recent_status_updates`, `recent_chat_messages`
- `recent_employees` (admins only), `recent_notifications`
- `quick_actions`: permission flags for UI

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/dashboard/recent \
  -H "Authorization: Bearer <token>"
```

---

#### `GET /api/v1/dashboard/employees`

Retrieve employee workload and performance analytics.

**Access:** Authenticated

**Scoping:** Admins see metrics for all employees. Counselors see only their own stats.

**Response:**

```json
{
  "success": true,
  "message": "Dashboard employee analytics retrieved successfully.",
  "data": [
    {
      "employee_id": 2,
      "name": "Jane Counsellor",
      "role": "employee",
      "applicants_assigned": 15,
      "completed_cases": 8,
      "pending_cases": 7,
      "documents_pending": 5,
      "documents_uploaded": 45,
      "average_processing_time": 12.5,
      "latest_login": "2026-07-14T08:00:00+00:00",
      "latest_logout": "2026-07-14T12:00:00+00:00"
    }
  ],
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/dashboard/employees \
  -H "Authorization: Bearer <token>"
```

---

#### `GET /api/v1/dashboard/system` (Admin)

Retrieve SQLite database performance parameters and system overview.

**Access:** Admin only

**Response:**

```json
{
  "success": true,
  "message": "System analytics parameters retrieved successfully.",
  "data": {
    "total_db_size_bytes": 2621440,
    "sqlite_version": "3.45.0",
    "system_uptime_seconds": 86400.0,
    "active_user_sessions": 5,
    "total_queries_logged": 1200
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl http://localhost:8000/api/v1/dashboard/system \
  -H "Authorization: Bearer <token>"
```

---

### 5.9 Activity Logs

Base: `/api/v1/activity-logs`

#### `GET /api/v1/activity-logs` (Admin)

Retrieve paginated audit logs for login/logout events.

**Access:** Admin only

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | `integer` | — | Filter by specific user ID |
| `page` | `integer` | `1` | Page number (1-indexed) |
| `page_size` | `integer` | `20` | Items per page (max 100) |

**Response:**

```json
{
  "success": true,
  "message": "Activity logs retrieved successfully.",
  "data": {
    "total_count": 150,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "user_id": 1,
        "employee_name": "Admin User",
        "employee_code": "EMP-000001",
        "login_time": "2026-07-14T08:00:00+00:00",
        "logout_time": "2026-07-14T12:00:00+00:00",
        "ip_address": "192.168.1.100",
        "browser": "Mozilla/5.0 ...",
        "device": null
      }
    ]
  },
  "error": null,
  "errors": null,
  "timestamp": "...",
  "request_id": "..."
}
```

**cURL Example:**

```bash
curl "http://localhost:8000/api/v1/activity-logs?page=1&page_size=20" \
  -H "Authorization: Bearer <token>"
```

---

### 5.10 Infrastructure

#### `GET /health`

Basic health check.

**Response:**

```json
{
  "status": "healthy",
  "app": "Ready2Go CRM",
  "version": "1.0.0"
}
```

**cURL Example:**

```bash
curl http://localhost:8000/health
```

---

#### `GET /ready`

Readiness probe — verifies the app can serve traffic and the database is connected.

**Response (healthy):**

```json
{
  "status": "ready",
  "database": "connected"
}
```

**Response (unhealthy) — `503 Service Unavailable`:**

```json
{
  "status": "not ready",
  "database": "disconnected"
}
```

**cURL Example:**

```bash
curl http://localhost:8000/ready
```

---

#### `GET /live`

Liveness probe — confirms the process is alive.

**Response:**

```json
{
  "status": "alive"
}
```

**cURL Example:**

```bash
curl http://localhost:8000/live
```

---

#### `GET /version`

Return version and build information.

**Response:**

```json
{
  "app": "Ready2Go CRM",
  "version": "1.0.0",
  "environment": "development"
}
```

**cURL Example:**

```bash
curl http://localhost:8000/version
```

---

## 6. Pagination

### 6.1 Request Format

Paginated endpoints accept two standard query parameters:

| Parameter | Type | Default | Minimum | Maximum | Description |
|-----------|------|---------|---------|---------|-------------|
| `page` | `integer` | `1` | `1` | — | 1-indexed page number |
| `page_size` | `integer` | `10` or `20` | `1` | `100` | Items per page |

> Note: `page_size` defaults to `10` for employee/notification lists and `20` for applicant lists. All endpoint defaults cap at `MAX_PAGE_SIZE = 100`.

### 6.2 Response Format

Paginated responses return an envelope with:

```json
{
  "data": {
    "total_count": 150,
    "page": 1,
    "page_size": 20,
    "items": [ ... ]
  }
}
```

For applicants specifically:

```json
{
  "data": {
    "applicants": [ ... ],
    "total": 150,
    "page": 1,
    "page_size": 20,
    "total_pages": 8
  }
}
```

### 6.3 Offset Calculation

Offset is calculated as: `offset = (page - 1) * page_size`

---

## 7. Filters and Search

### 7.1 Query Parameter Filters

Endpoints that support filtering accept parameters as query strings:

| Endpoint | Filter Parameters |
|----------|-------------------|
| `GET /api/v1/applicants` | `visa_type`, `status`, `country`, `assigned_to` |
| `GET /api/v1/employees` | `role`, `department`, `is_active` |
| `GET /api/v1/activity-logs` | `user_id` |

### 7.2 Search

Search is a case-insensitive partial match across multiple columns via the `search` query parameter:

| Endpoint | Searchable Columns |
|----------|--------------------|
| `GET /api/v1/applicants` | `applicant_code`, `full_name`, `email`, `phone` |
| `GET /api/v1/employees` | `name`, `email`, `employee_code`, `department` |

### 7.3 Combined Example

```
GET /api/v1/applicants?visa_type=student&status=inquiry&country=India&search=john&page=1&page_size=20
```

---

## 8. File Uploads

### 8.1 Request Format

File uploads use `multipart/form-data` encoding.

### 8.2 Allowed File Types

| Extension | MIME Type |
|-----------|-----------|
| `.pdf` | `application/pdf` |
| `.jpg` | `image/jpeg` |
| `.jpeg` | `image/jpeg` |
| `.png` | `image/png` |
| `.doc` | `application/msword` |
| `.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |

### 8.3 Size Limit

Maximum file size: **500 MB** (configurable via `MAX_UPLOAD_SIZE_MB`).

### 8.4 Storage

Files are stored in a Supabase Storage bucket (`ready2go-documents`) or a local `uploads/` directory in development mode. All documents are organized under `applicants/{applicant_code}/{uuid_filename}` path structure.

### 8.5 Document Types

Valid document type values:

| Value | Description |
|-------|-------------|
| `passport` | Passport scan |
| `national_id` | National ID card |
| `photograph` | Passport-size photograph |
| `academic_certificate` | Academic transcripts/certificates |
| `ielts` | IELTS test report |
| `toefl` | TOEFL test report |
| `offer_letter` | University/college offer letter |
| `bank_statement` | Bank statement |
| `financial_proof` | Financial proof documents |
| `visa_application` | Visa application form |
| `insurance` | Insurance documents |
| `employment_proof` | Employment proof |
| `travel_itinerary` | Travel itinerary |
| `other` | Other documents |

### 8.6 Security

- In production, uploaded files are never served directly from the filesystem. They are served exclusively via short-lived signed URLs.
- In development mode, files may be served from `/uploads` mount point.
- Document download/view URLs expire after 60 minutes by default.

---

## 9. Role-Based Access Control (RBAC)

### 9.1 Roles

| Role | Description |
|------|-------------|
| `admin` | Full system access — can manage employees, view all data, access system metrics |
| `employee` | Operational access — can manage applicants, documents, chat, and their own profile |

### 9.2 Access Matrix

| Module | Endpoint | Admin | Employee |
|--------|----------|-------|----------|
| **Auth** | `POST /auth/login` | Yes | Yes |
| | `GET /auth/me` | Yes | Yes |
| | `POST /auth/logout` | Yes | Yes |
| **Employees** | `GET /employees` | Yes | No |
| | `POST /employees` | Yes | No |
| | `GET /employees/{id}` | Yes | No |
| | `PUT /employees/{id}` | Yes | No |
| | `PATCH /employees/{id}/status` | Yes | No |
| | `PATCH /employees/{id}/reset-password` | Yes | No |
| | `GET /employees/profile/me` | Yes | Yes |
| | `PUT /employees/profile/me` | Yes | Yes |
| **Applicants** | `GET /applicants` | Yes (all) | Yes (all)* |
| | `POST /applicants` | Yes | Yes |
| | `GET /applicants/{id}` | Yes | Yes |
| | `PUT /applicants/{id}` | Yes | Yes |
| | `DELETE /applicants/{id}` | Yes | Yes |
| **Documents** | All document endpoints | Yes | Yes |
| **Progress** | All progress endpoints | Yes | Yes |
| **Chat** | `DELETE /chat/{id}` | Yes (any message) | Yes (own messages only) |
| | Other chat endpoints | Yes | Yes |
| **Notifications** | All notification endpoints | Yes (own + system-wide) | Yes (own only) |
| **Dashboard** | `GET /dashboard/summary` | Yes | Yes (scoped) |
| | `GET /dashboard/charts` | Yes (global) | Yes (scoped) |
| | `GET /dashboard/recent` | Yes (global) | Yes (scoped) |
| | `GET /dashboard/employees` | Yes (all) | Yes (self only) |
| | `GET /dashboard/system` | Yes | No |
| **Activity Logs** | `GET /activity-logs` | Yes | No |
| **Infrastructure** | All health/readiness endpoints | Yes | Yes |

> *Applicant listing is not scoped by default — employees can view all non-deleted applicants. Dashboard scoping only applies to chart/recent/employee analytics data.

### 9.3 Authorization Enforcement

- **JWT required:** All endpoints except `/health`, `/ready`, `/live`, `/version`, and `/auth/login`.
- **Admin required:** All employee management endpoints (except `/profile/me`), activity logs, and system dashboard.
- **Self-deactivation prohibited:** Admins cannot deactivate their own account.
- **Message deletion:** Non-admin users can only delete messages they authored.
- **Notification visibility:** Employees see only their own notifications; admins see system-wide notifications as well.

---

## 10. Common Request/Response Examples

### 10.1 Full Authentication Flow

**Step 1: Login**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@ready2go.com", "password": "secret123"}'
```

**Step 2: Extract token and use for subsequent requests**

```bash
# Save token
TOKEN="eyJhbGciOiJIUzI1NiIs..."

# Get profile
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# List applicants
curl "http://localhost:8000/api/v1/applicants?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

### 10.2 Complete Applicant Lifecycle

```bash
TOKEN="<your-jwt-token>"

# 1. Create applicant
curl -X POST http://localhost:8000/api/v1/applicants \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Alice Smith",
    "email": "alice@example.com",
    "phone": "+919876543210",
    "country": "India",
    "visa_type": "student",
    "status": "inquiry"
  }'

# 2. Update progress to documents_pending
curl -X PUT http://localhost:8000/api/v1/progress/applicant/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "documents_pending", "remarks": "Documents requested."}'

# 3. Upload a document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@passport.pdf" \
  -F "applicant_id=1" \
  -F "document_type=passport"

# 4. Send a chat message
curl -X POST http://localhost:8000/api/v1/chat/applicant/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Documents received, moving to next stage."}'

# 5. Get progress timeline
curl http://localhost:8000/api/v1/progress/applicant/1 \
  -H "Authorization: Bearer $TOKEN"

# 6. Get conversation
curl http://localhost:8000/api/v1/chat/applicant/1 \
  -H "Authorization: Bearer $TOKEN"
```

### 10.3 Error Handling Pattern

```bash
# Invalid login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "nonexistent@test.com", "password": "wrong"}'
# Response: 401 with error: "UNAUTHORIZED"

# Access without token
curl http://localhost:8000/api/v1/applicants
# Response: 401 with error: "UNAUTHORIZED"

# Admin endpoint as employee
curl http://localhost:8000/api/v1/employees \
  -H "Authorization: Bearer $EMPLOYEE_TOKEN"
# Response: 403 with message: "Admin access required."

# Invalid status transition
curl -X PUT http://localhost:8000/api/v1/progress/applicant/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "visa_approved", "remarks": "Direct approval"}'
# Response: 400 with message about invalid transition

# Validation error
curl -X POST http://localhost:8000/api/v1/applicants \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "", "visa_type": "invalid"}'
# Response: 422 with field-level errors

# Deactivated account
# Response: 403 with message: "Account has been deactivated."
```

### 10.4 Paginated Search Request

```bash
curl "http://localhost:8000/api/v1/applicants?visa_type=student&search=alice&page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

### 10.5 Notification Management

```bash
TOKEN="<your-jwt-token>"

# Check unread count
curl http://localhost:8000/api/v1/notifications/unread-count \
  -H "Authorization: Bearer $TOKEN"

# List notifications
curl "http://localhost:8000/api/v1/notifications?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# Mark one as read
curl -X PATCH http://localhost:8000/api/v1/notifications/5/read \
  -H "Authorization: Bearer $TOKEN"

# Mark all as read
curl -X PATCH http://localhost:8000/api/v1/notifications/read-all \
  -H "Authorization: Bearer $TOKEN"
```

---

## Appendices

### A. Application Status Values

| Status | Description |
|--------|-------------|
| `inquiry` | Initial inquiry received |
| `documents_pending` | Documents requested, awaiting submission |
| `documents_submitted` | All required documents submitted |
| `application_processing` | Application being processed |
| `under_review` | Application under review |
| `interview_scheduled` | Interview scheduled |
| `visa_approved` | Visa approved |
| `visa_rejected` | Visa rejected |
| `approved` | Application approved |
| `visa_issued` | Visa issued |
| `rejected` | Application rejected |
| `cancelled` | Application cancelled |
| `completed` | Process completed |

### B. Visa Type Values

| Value | Description |
|-------|-------------|
| `student` | Student visa |
| `visit` | Visit visa |
| `tourist` | Tourist visa |
| `business` | Business visa |

### C. Notification Types

| Value | Description |
|-------|-------------|
| `info` | Informational notification |
| `success` | Success notification |
| `warning` | Warning notification |
| `error` | Error notification |

### D. Notification Priority Levels

| Value | Description |
|-------|-------------|
| `low` | Low priority |
| `medium` | Medium priority |
| `high` | High priority |

### E. Chat Message Types

| Value | Description |
|-------|-------------|
| `text` | Regular text message |
| `attachment` | Message with file attachment |
| `system` | Auto-generated system message |

### F. Configuration Reference

| Config Key | Default | Description |
|------------|---------|-------------|
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT token lifetime in minutes |
| `MAX_UPLOAD_SIZE_MB` | `500` | Maximum file upload size in MB |
| `SIGNED_URL_EXPIRY_MINUTES` | `60` | Document signed URL lifetime in minutes |
| `ALLOWED_DOCUMENT_TYPES` | `pdf,jpg,jpeg,png,doc,docx` | Comma-separated allowed file extensions |
| `DEFAULT_PAGE_SIZE` | `10` | Default items per page for pagination |
| `MAX_PAGE_SIZE` | `100` | Maximum items per page |
| `ENABLE_SOFT_DELETE` | `true` | Feature flag for soft-delete functionality |
| `SUPABASE_BUCKET` | `ready2go-documents` | Supabase Storage bucket name |

### G. HTTP Status Code Usage

| Status Code | Usage |
|-------------|-------|
| `200 OK` | Successful GET, PUT, PATCH, DELETE requests |
| `201 Created` | Successful POST requests (create operations) |
| `400 Bad Request` | Invalid input, duplicate email, invalid transition, self-deactivation |
| `401 Unauthorized` | Missing, invalid, or expired JWT token |
| `403 Forbidden` | Insufficient role permissions or deactivated account |
| `404 Not Found` | Resource does not exist or has been deleted |
| `422 Unprocessable Entity` | Request body validation failure |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Unhandled server-side error |
| `503 Service Unavailable` | Readiness check failure (database disconnected) |
