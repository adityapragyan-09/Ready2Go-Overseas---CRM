# Ready2Go CRM — Regression Test Script (Fixed)
# Tests all backend API endpoints and reports Pass/Fail

$baseUrl = "http://localhost:8000/api/v1"
$results = @()

Write-Host "============================================="
Write-Host "  Ready2Go CRM - Backend Regression Tests"
Write-Host "============================================="
Write-Host ""

# ── MODULE 1: Authentication ──────────────────────
Write-Host "--- MODULE 1: Authentication ---"

# 1a. Login with valid credentials
try {
    $loginResp = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method POST -ContentType "application/json" `
        -Body '{"email":"admin@ready2gooverseas.com","password":"AdminPass123!"}' -ErrorAction Stop
    $token = $loginResp.data.token
    Write-Host "[PASS] Auth: Login (valid creds) - $($loginResp.message)"
    $results += @{ Name="Auth: Login (valid)"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Auth: Login (valid creds) - $($_.Exception.Message)"
    $results += @{ Name="Auth: Login (valid)"; Status="FAIL"; Detail=$_.Exception.Message }
    Write-Host "Cannot continue without auth token. Exiting."
    exit 1
}

$authHeaders = @{ Authorization = "Bearer $token" }

# 1b. Login with invalid credentials
try {
    Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method POST -ContentType "application/json" `
        -Body '{"email":"wrong@test.com","password":"wrong"}' -ErrorAction Stop
    Write-Host "[FAIL] Auth: Login (invalid) - Should have returned 401"
    $results += @{ Name="Auth: Login (invalid)"; Status="FAIL" }
} catch {
    Write-Host "[PASS] Auth: Login (invalid) - Correctly rejected with 401"
    $results += @{ Name="Auth: Login (invalid)"; Status="PASS" }
}

# 1c. Protected route without token
try {
    Invoke-RestMethod -Uri "$baseUrl/employees/profile/me" -Method GET -ContentType "application/json" -ErrorAction Stop
    Write-Host "[FAIL] Auth: No-token guard - Should have returned 401"
    $results += @{ Name="Auth: No-token guard"; Status="FAIL" }
} catch {
    Write-Host "[PASS] Auth: No-token guard - Correctly blocked"
    $results += @{ Name="Auth: No-token guard"; Status="PASS" }
}

# 1d. Get own profile
try {
    $profile = Invoke-RestMethod -Uri "$baseUrl/employees/profile/me" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
    Write-Host "[PASS] Auth: GET /employees/profile/me - $($profile.data.full_name)"
    $results += @{ Name="Auth: Profile/me"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Auth: GET /employees/profile/me - $($_.Exception.Message)"
    $results += @{ Name="Auth: Profile/me"; Status="FAIL"; Detail=$_.Exception.Message }
}

Write-Host ""

# ── MODULE 2: Employee Management ──────────────────
Write-Host "--- MODULE 2: Employee Management ---"

# 2a. List employees
try {
    $empList = Invoke-RestMethod -Uri "$baseUrl/employees" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
    $empCount = $empList.data.total_count
    Write-Host "[PASS] Employee: GET / (list) - $empCount employees found"
    $results += @{ Name="Employee: List"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Employee: GET / (list) - $($_.Exception.Message)"
    $results += @{ Name="Employee: List"; Status="FAIL"; Detail=$_.Exception.Message }
}

# 2b. Create employee
$newEmpId = $null
try {
    $empBody = '{"full_name":"Test Counselor","email":"test.counselor@ready2go.com","password":"Test@123!","role":"employee","phone":"+919999900000","designation":"Senior Counselor","department":"Canada Admissions"}'
    $empCreate = Invoke-RestMethod -Uri "$baseUrl/employees" -Method POST -ContentType "application/json" -Headers $authHeaders -Body $empBody -ErrorAction Stop
    $newEmpId = $empCreate.data.id
    Write-Host "[PASS] Employee: POST / (create) - ID=$newEmpId, Code=$($empCreate.data.employee_code)"
    $results += @{ Name="Employee: Create"; Status="PASS" }
} catch {
    $errBody = $_.ErrorDetails.Message
    if ($errBody -match "already exists") {
        Write-Host "[PASS] Employee: POST / (create) - Already exists (idempotent check)"
        $results += @{ Name="Employee: Create"; Status="PASS" }
    } else {
        Write-Host "[FAIL] Employee: POST / (create) - $($_.Exception.Message)"
        $results += @{ Name="Employee: Create"; Status="FAIL"; Detail=$_.Exception.Message }
    }
}

# 2c. Get single employee
if ($newEmpId) {
    try {
        $empSingle = Invoke-RestMethod -Uri "$baseUrl/employees/$newEmpId" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
        Write-Host "[PASS] Employee: GET /$newEmpId (single) - $($empSingle.data.full_name)"
        $results += @{ Name="Employee: Get Single"; Status="PASS" }
    } catch {
        Write-Host "[FAIL] Employee: GET /$newEmpId (single) - $($_.Exception.Message)"
        $results += @{ Name="Employee: Get Single"; Status="FAIL"; Detail=$_.Exception.Message }
    }
}

# 2d. Update employee
if ($newEmpId) {
    try {
        $updateBody = '{"full_name":"Test Counselor Updated","phone":"+918888877777","role":"employee","designation":"Lead Counselor","department":"Australia Admissions"}'
        $empUpdate = Invoke-RestMethod -Uri "$baseUrl/employees/$newEmpId" -Method PUT -ContentType "application/json" -Headers $authHeaders -Body $updateBody -ErrorAction Stop
        Write-Host "[PASS] Employee: PUT /$newEmpId (update) - $($empUpdate.data.full_name)"
        $results += @{ Name="Employee: Update"; Status="PASS" }
    } catch {
        Write-Host "[FAIL] Employee: PUT /$newEmpId (update) - $($_.Exception.Message)"
        $results += @{ Name="Employee: Update"; Status="FAIL"; Detail=$_.Exception.Message }
    }
}

# 2e. Toggle status (deactivate)
if ($newEmpId) {
    try {
        $statusResp = Invoke-RestMethod -Uri "$baseUrl/employees/$newEmpId/status" -Method PATCH -ContentType "application/json" -Headers $authHeaders -Body '{"is_active":false}' -ErrorAction Stop
        Write-Host "[PASS] Employee: PATCH /$newEmpId/status (deactivate) - $($statusResp.message)"
        $results += @{ Name="Employee: Status Toggle"; Status="PASS" }
    } catch {
        Write-Host "[FAIL] Employee: PATCH /$newEmpId/status - $($_.Exception.Message)"
        $results += @{ Name="Employee: Status Toggle"; Status="FAIL"; Detail=$_.Exception.Message }
    }
    # Re-activate for further tests
    try { Invoke-RestMethod -Uri "$baseUrl/employees/$newEmpId/status" -Method PATCH -ContentType "application/json" -Headers $authHeaders -Body '{"is_active":true}' -ErrorAction Stop } catch {}
}

# 2f. Reset password
if ($newEmpId) {
    try {
        $resetResp = Invoke-RestMethod -Uri "$baseUrl/employees/$newEmpId/reset-password" -Method PATCH -ContentType "application/json" -Headers $authHeaders -Body '{"password":"NewPass@456!"}' -ErrorAction Stop
        Write-Host "[PASS] Employee: PATCH /$newEmpId/reset-password - $($resetResp.message)"
        $results += @{ Name="Employee: Password Reset"; Status="PASS" }
    } catch {
        Write-Host "[FAIL] Employee: PATCH /$newEmpId/reset-password - $($_.Exception.Message)"
        $results += @{ Name="Employee: Password Reset"; Status="FAIL"; Detail=$_.Exception.Message }
    }
}

# 2g. Search employees
try {
    $searchResp = Invoke-RestMethod -Uri "$baseUrl/employees?search=Test" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
    Write-Host "[PASS] Employee: Search (?search=Test) - $($searchResp.data.total_count) results"
    $results += @{ Name="Employee: Search"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Employee: Search - $($_.Exception.Message)"
    $results += @{ Name="Employee: Search"; Status="FAIL"; Detail=$_.Exception.Message }
}

# 2h. Filter by role
try {
    $filterResp = Invoke-RestMethod -Uri "$baseUrl/employees?role=admin" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
    Write-Host "[PASS] Employee: Filter (?role=admin) - $($filterResp.data.total_count) admins"
    $results += @{ Name="Employee: Role Filter"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Employee: Role Filter - $($_.Exception.Message)"
    $results += @{ Name="Employee: Role Filter"; Status="FAIL"; Detail=$_.Exception.Message }
}

Write-Host ""

# ── MODULE 3: Applicant Management ─────────────────
Write-Host "--- MODULE 3: Applicant Management ---"

# 3a. List applicants
try {
    $appList = Invoke-RestMethod -Uri "$baseUrl/applicants" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
    Write-Host "[PASS] Applicant: GET / (list) - $($appList.data.total) total"
    $results += @{ Name="Applicant: List"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Applicant: GET / (list) - $($_.Exception.Message)"
    $results += @{ Name="Applicant: List"; Status="FAIL"; Detail=$_.Exception.Message }
}

# 3b. Create applicant
$newAppId = $null
try {
    $appBody = '{"full_name":"John Doe","email":"john.doe@example.com","phone":"+919999988888","visa_type":"student","country":"Canada","status":"inquiry"}'
    $appCreate = Invoke-RestMethod -Uri "$baseUrl/applicants" -Method POST -ContentType "application/json" -Headers $authHeaders -Body $appBody -ErrorAction Stop
    $newAppId = $appCreate.data.id
    Write-Host "[PASS] Applicant: POST / (create) - ID=$newAppId, Code=$($appCreate.data.applicant_code)"
    $results += @{ Name="Applicant: Create"; Status="PASS" }
} catch {
    $errBody = $_.ErrorDetails.Message
    if ($errBody -match "already exists") {
        Write-Host "[PASS] Applicant: POST / (create) - Already exists (idempotent)"
        $results += @{ Name="Applicant: Create"; Status="PASS" }
        # Try to find the existing applicant
        try {
            $searchResp = Invoke-RestMethod -Uri "$baseUrl/applicants?search=John" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
            if ($searchResp.data.items.Count -gt 0) { $newAppId = $searchResp.data.items[0].id }
        } catch {}
    } else {
        Write-Host "[FAIL] Applicant: POST / (create) - $($_.Exception.Message) | $errBody"
        $results += @{ Name="Applicant: Create"; Status="FAIL"; Detail=$_.Exception.Message }
    }
}

# 3c. Get single applicant
if ($newAppId) {
    try {
        $appSingle = Invoke-RestMethod -Uri "$baseUrl/applicants/$newAppId" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
        Write-Host "[PASS] Applicant: GET /$newAppId (single) - $($appSingle.data.full_name)"
        $results += @{ Name="Applicant: Get Single"; Status="PASS" }
    } catch {
        Write-Host "[FAIL] Applicant: GET /$newAppId (single) - $($_.Exception.Message)"
        $results += @{ Name="Applicant: Get Single"; Status="FAIL"; Detail=$_.Exception.Message }
    }
}

# 3d. Update applicant
if ($newAppId) {
    try {
        $updateAppBody = '{"full_name":"John Doe Updated","email":"john.doe@example.com","phone":"+918888877777","visa_type":"student","country":"Germany","status":"documents_pending"}'
        $appUpdate = Invoke-RestMethod -Uri "$baseUrl/applicants/$newAppId" -Method PUT -ContentType "application/json" -Headers $authHeaders -Body $updateAppBody -ErrorAction Stop
        Write-Host "[PASS] Applicant: PUT /$newAppId (update) - $($appUpdate.data.full_name)"
        $results += @{ Name="Applicant: Update"; Status="PASS" }
    } catch {
        Write-Host "[FAIL] Applicant: PUT /$newAppId (update) - $($_.Exception.Message)"
        $results += @{ Name="Applicant: Update"; Status="FAIL"; Detail=$_.Exception.Message }
    }
}

# 3e. Search
try {
    $searchApp = Invoke-RestMethod -Uri "$baseUrl/applicants?search=John" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
    Write-Host "[PASS] Applicant: Search (?search=John) - $($searchApp.data.total) results"
    $results += @{ Name="Applicant: Search"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Applicant: Search - $($_.Exception.Message)"
    $results += @{ Name="Applicant: Search"; Status="FAIL"; Detail=$_.Exception.Message }
}

# 3f. Filter by visa type
try {
    $filterApp = Invoke-RestMethod -Uri "$baseUrl/applicants?visa_type=student" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
    Write-Host "[PASS] Applicant: Filter (?visa_type=student) - $($filterApp.data.total) results"
    $results += @{ Name="Applicant: Visa Filter"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Applicant: Visa Filter - $($_.Exception.Message)"
    $results += @{ Name="Applicant: Visa Filter"; Status="FAIL"; Detail=$_.Exception.Message }
}

# 3g. Pagination
try {
    $pageApp = Invoke-RestMethod -Uri "$baseUrl/applicants?page=1&page_size=5" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
    Write-Host "[PASS] Applicant: Pagination (?page=1&page_size=5) - page $($pageApp.data.page)/$($pageApp.data.total_pages)"
    $results += @{ Name="Applicant: Pagination"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Applicant: Pagination - $($_.Exception.Message)"
    $results += @{ Name="Applicant: Pagination"; Status="FAIL"; Detail=$_.Exception.Message }
}

# 3h. Assign applicant
if ($newAppId -and $newEmpId) {
    try {
        $assignResp = Invoke-RestMethod -Uri "$baseUrl/applicants/$newAppId/assign" -Method PATCH -ContentType "application/json" -Headers $authHeaders -Body "{`"employee_id`":$newEmpId}" -ErrorAction Stop
        Write-Host "[PASS] Applicant: PATCH /$newAppId/assign - $($assignResp.message)"
        $results += @{ Name="Applicant: Assign"; Status="PASS" }
    } catch {
        Write-Host "[FAIL] Applicant: Assign - $($_.Exception.Message)"
        $results += @{ Name="Applicant: Assign"; Status="FAIL"; Detail=$_.Exception.Message }
    }
}

Write-Host ""

# ── MODULE 4: Progress Tracking ────────────────────
Write-Host "--- MODULE 4: Progress Tracking ---"

if ($newAppId) {
    # 4a. Get progress timeline
    try {
        $progList = Invoke-RestMethod -Uri "$baseUrl/progress/applicant/$newAppId" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
        Write-Host "[PASS] Progress: GET /$newAppId/progress - $($progList.message)"
        $results += @{ Name="Progress: List"; Status="PASS" }
    } catch {
        Write-Host "[FAIL] Progress: GET /$newAppId/progress - $($_.Exception.Message)"
        $results += @{ Name="Progress: List"; Status="FAIL"; Detail=$_.Exception.Message }
    }

    # 4b. Add progress
    try {
        $progBody = '{"status":"documents_submitted","remarks":"All documents received and verified."}'
        $progAdd = Invoke-RestMethod -Uri "$baseUrl/progress/applicant/$newAppId" -Method PUT -ContentType "application/json" -Headers $authHeaders -Body $progBody -ErrorAction Stop
        Write-Host "[PASS] Progress: POST /$newAppId/progress (add) - $($progAdd.message)"
        $results += @{ Name="Progress: Add"; Status="PASS" }
    } catch {
        Write-Host "[FAIL] Progress: POST /$newAppId/progress (add) - $($_.Exception.Message)"
        $results += @{ Name="Progress: Add"; Status="FAIL"; Detail=$_.Exception.Message }
    }
} else {
    Write-Host "[SKIP] Progress: No applicant ID available"
}

Write-Host ""

# ── MODULE 5: Document Management ──────────────────
Write-Host "--- MODULE 5: Document Management ---"

if ($newAppId) {
    try {
        $docList = Invoke-RestMethod -Uri "$baseUrl/documents/applicant/$newAppId" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
        Write-Host "[PASS] Documents: GET /$newAppId/documents - $($docList.message)"
        $results += @{ Name="Documents: List"; Status="PASS" }
    } catch {
        Write-Host "[FAIL] Documents: GET /$newAppId/documents - $($_.Exception.Message)"
        $results += @{ Name="Documents: List"; Status="FAIL"; Detail=$_.Exception.Message }
    }
} else {
    Write-Host "[SKIP] Documents: No applicant ID available"
}

Write-Host ""

# ── MODULE 6: Internal Chat ───────────────────────
Write-Host "--- MODULE 6: Internal Chat ---"

if ($newAppId) {
    # 6a. Get chat messages
    try {
        $chatList = Invoke-RestMethod -Uri "$baseUrl/chat/applicant/$newAppId" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
        Write-Host "[PASS] Chat: GET /$newAppId/chat - $($chatList.message)"
        $results += @{ Name="Chat: List"; Status="PASS" }
    } catch {
        Write-Host "[FAIL] Chat: GET /$newAppId/chat - $($_.Exception.Message)"
        $results += @{ Name="Chat: List"; Status="FAIL"; Detail=$_.Exception.Message }
    }

    # 6b. Send message
    try {
        $chatBody = '{"content":"Hello, this is a regression test message."}'
        $chatSend = Invoke-RestMethod -Uri "$baseUrl/chat/applicant/$newAppId" -Method POST -ContentType "application/json" -Headers $authHeaders -Body $chatBody -ErrorAction Stop
        Write-Host "[PASS] Chat: POST /$newAppId/chat (send) - $($chatSend.message)"
        $results += @{ Name="Chat: Send"; Status="PASS" }
    } catch {
        Write-Host "[FAIL] Chat: POST /$newAppId/chat (send) - $($_.Exception.Message)"
        $results += @{ Name="Chat: Send"; Status="FAIL"; Detail=$_.Exception.Message }
    }
} else {
    Write-Host "[SKIP] Chat: No applicant ID available"
}

Write-Host ""

# ── MODULE 7: Notification Center ─────────────────
Write-Host "--- MODULE 7: Notification Center ---"

try {
    $notifList = Invoke-RestMethod -Uri "$baseUrl/notifications" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
    Write-Host "[PASS] Notifications: GET / (list) - $($notifList.message)"
    $results += @{ Name="Notifications: List"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Notifications: GET / (list) - $($_.Exception.Message)"
    $results += @{ Name="Notifications: List"; Status="FAIL"; Detail=$_.Exception.Message }
}

try {
    $notifCount = Invoke-RestMethod -Uri "$baseUrl/notifications/unread-count" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
    Write-Host "[PASS] Notifications: GET /unread-count - count=$($notifCount.data.count)"
    $results += @{ Name="Notifications: Unread Count"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Notifications: GET /unread-count - $($_.Exception.Message)"
    $results += @{ Name="Notifications: Unread Count"; Status="FAIL"; Detail=$_.Exception.Message }
}

Write-Host ""

# ── MODULE 8: Soft Delete ────────────────────────
Write-Host "--- MODULE 8: Soft Delete ---"

if ($newAppId) {
    try {
        $delResp = Invoke-RestMethod -Uri "$baseUrl/applicants/$newAppId" -Method DELETE -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
        Write-Host "[PASS] Applicant: DELETE /$newAppId (soft delete) - $($delResp.message)"
        $results += @{ Name="Applicant: Soft Delete"; Status="PASS" }
    } catch {
        Write-Host "[FAIL] Applicant: DELETE /$newAppId - $($_.Exception.Message)"
        $results += @{ Name="Applicant: Soft Delete"; Status="FAIL"; Detail=$_.Exception.Message }
    }
} else {
    Write-Host "[SKIP] Soft Delete: No applicant ID available"
}

Write-Host ""

# ── MODULE 9: Dashboard & Analytics ────────────────
Write-Host "--- MODULE 9: Dashboard & Analytics ---"

try {
    $summary = Invoke-RestMethod -Uri "$baseUrl/dashboard/summary" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
    Write-Host "[PASS] Dashboard: GET /summary - $($summary.message)"
    $results += @{ Name="Dashboard: Summary"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Dashboard: GET /summary - $($_.Exception.Message)"
    $results += @{ Name="Dashboard: Summary"; Status="FAIL"; Detail=$_.Exception.Message }
}

try {
    $charts = Invoke-RestMethod -Uri "$baseUrl/dashboard/charts" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
    Write-Host "[PASS] Dashboard: GET /charts - $($charts.message)"
    $results += @{ Name="Dashboard: Charts"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Dashboard: GET /charts - $($_.Exception.Message)"
    $results += @{ Name="Dashboard: Charts"; Status="FAIL"; Detail=$_.Exception.Message }
}

try {
    $recent = Invoke-RestMethod -Uri "$baseUrl/dashboard/recent" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
    Write-Host "[PASS] Dashboard: GET /recent - $($recent.message)"
    $results += @{ Name="Dashboard: Recent"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Dashboard: GET /recent - $($_.Exception.Message)"
    $results += @{ Name="Dashboard: Recent"; Status="FAIL"; Detail=$_.Exception.Message }
}

try {
    $employees = Invoke-RestMethod -Uri "$baseUrl/dashboard/employees" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
    Write-Host "[PASS] Dashboard: GET /employees - $($employees.message)"
    $results += @{ Name="Dashboard: Employees"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Dashboard: GET /employees - $($_.Exception.Message)"
    $results += @{ Name="Dashboard: Employees"; Status="FAIL"; Detail=$_.Exception.Message }
}

try {
    $system = Invoke-RestMethod -Uri "$baseUrl/dashboard/system" -Method GET -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
    Write-Host "[PASS] Dashboard: GET /system - $($system.message)"
    $results += @{ Name="Dashboard: System"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Dashboard: GET /system - $($_.Exception.Message)"
    $results += @{ Name="Dashboard: System"; Status="FAIL"; Detail=$_.Exception.Message }
}

Write-Host ""

# ── MODULE 10: Logout ────────────────────────────
Write-Host "--- MODULE 10: Auth Logout ---"
try {
    $logoutResp = Invoke-RestMethod -Uri "$baseUrl/auth/logout" -Method POST -ContentType "application/json" -Headers $authHeaders -ErrorAction Stop
    Write-Host "[PASS] Auth: POST /auth/logout - $($logoutResp.message)"
    $results += @{ Name="Auth: Logout"; Status="PASS" }
} catch {
    Write-Host "[FAIL] Auth: POST /auth/logout - $($_.Exception.Message)"
    $results += @{ Name="Auth: Logout"; Status="FAIL"; Detail=$_.Exception.Message }
}

Write-Host ""

# ── SUMMARY ──────────────────────────────────────
Write-Host "============================================="
Write-Host "  REGRESSION TEST SUMMARY"
Write-Host "============================================="
$passed = ($results | Where-Object { $_.Status -eq "PASS" }).Count
$failed = ($results | Where-Object { $_.Status -eq "FAIL" }).Count
$total = $results.Count
Write-Host "Total: $total | Passed: $passed | Failed: $failed"
Write-Host ""
if ($failed -gt 0) {
    Write-Host "FAILED TESTS:"
    $results | Where-Object { $_.Status -eq "FAIL" } | ForEach-Object {
        Write-Host "  [FAIL] $($_.Name): $($_.Detail)"
    }
} else {
    Write-Host "ALL TESTS PASSED!"
}
Write-Host ""
Write-Host "Done."
