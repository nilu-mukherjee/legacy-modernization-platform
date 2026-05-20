# =============================================================================
# CodeLens AI — API Documentation
# =============================================================================
# Comprehensive API reference for the CodeLens AI backend.
# All endpoints are prefixed with /api/v1 unless otherwise noted.
# =============================================================================

# API Reference

## Overview

The CodeLens AI API is a RESTful JSON API built with FastAPI. All requests and
responses use JSON format.

### Base URL

```
Development: http://localhost:8000/api/v1
Production:  https://api.codelens.ai/api/v1
```

### Authentication

All protected endpoints require a JWT token in the Authorization header:

```http
Authorization: Bearer <jwt_token>
```

Tokens are obtained through the GitHub OAuth flow managed by Auth.js on the
frontend. The backend validates tokens using the shared AUTH_SECRET.

### Response Format

All responses follow a consistent format:

**Success:**
```json
{
  "data": { ... },
  "message": "Success"
}
```

**Error:**
```json
{
  "detail": "Error description",
  "status_code": 400
}
```

### Pagination

List endpoints support pagination:

```
GET /projects?skip=0&limit=20
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | int | 0 | Number of records to skip |
| `limit` | int | 20 | Maximum records to return (max 100) |

---

## Health Check

### `GET /health`

Check API health and database connectivity.

**Auth Required:** No

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected",
  "redis": "connected"
}
```

---

## Authentication

### `POST /api/v1/auth/sync`

Sync or create a user from GitHub OAuth. Called by the frontend after
successful GitHub authentication.

**Auth Required:** No (called with GitHub token)

**Request Body:**
```json
{
  "github_id": "12345",
  "email": "user@example.com",
  "name": "Jane Developer",
  "avatar_url": "https://avatars.githubusercontent.com/u/12345",
  "access_token": "gho_xxxxxxxxxxxx"
}
```

**Response (200):**
```json
{
  "id": "uuid-v4",
  "email": "user@example.com",
  "name": "Jane Developer",
  "avatar_url": "https://avatars.githubusercontent.com/u/12345",
  "created_at": "2026-01-01T00:00:00Z",
  "token": "jwt-token-here"
}
```

---

### `GET /api/v1/auth/me`

Get the currently authenticated user's profile.

**Auth Required:** Yes

**Response (200):**
```json
{
  "id": "uuid-v4",
  "email": "user@example.com",
  "name": "Jane Developer",
  "avatar_url": "https://avatars.githubusercontent.com/u/12345",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-15T12:00:00Z"
}
```

---

## Projects

### `GET /api/v1/projects`

List all projects for the authenticated user.

**Auth Required:** Yes

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 20 | Max results |
| `status` | string | null | Filter by status |

**Response (200):**
```json
{
  "projects": [
    {
      "id": "uuid-v4",
      "name": "legacy-api",
      "repo_url": "https://github.com/user/legacy-api",
      "repo_full_name": "user/legacy-api",
      "status": "completed",
      "detected_languages": {"python": 45, "javascript": 12},
      "total_files": 342,
      "total_loc": 28500,
      "last_analyzed_at": "2026-01-15T12:00:00Z",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 4
}
```

---

### `POST /api/v1/projects`

Create a new project and trigger analysis.

**Auth Required:** Yes

**Request Body:**
```json
{
  "repo_url": "https://github.com/user/legacy-api",
  "name": "Legacy API"  // optional, defaults to repo name
}
```

**Response (201):**
```json
{
  "id": "uuid-v4",
  "name": "Legacy API",
  "repo_url": "https://github.com/user/legacy-api",
  "status": "analyzing",
  "job_id": "uuid-v4",
  "created_at": "2026-01-15T12:00:00Z"
}
```

**Errors:**
| Code | Description |
|------|-------------|
| 400 | Invalid repository URL |
| 409 | Repository already added |
| 422 | Validation error |

---

### `GET /api/v1/projects/{project_id}`

Get detailed project information.

**Auth Required:** Yes

**Response (200):**
```json
{
  "id": "uuid-v4",
  "name": "Legacy API",
  "repo_url": "https://github.com/user/legacy-api",
  "repo_full_name": "user/legacy-api",
  "default_branch": "main",
  "description": "Legacy REST API service",
  "detected_languages": {"python": 45, "javascript": 12, "sql": 5},
  "total_files": 342,
  "total_loc": 28500,
  "status": "completed",
  "last_analyzed_at": "2026-01-15T12:00:00Z",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-15T12:00:00Z"
}
```

---

### `DELETE /api/v1/projects/{project_id}`

Delete a project and all associated analysis data.

**Auth Required:** Yes

**Response (204):** No content

---

### `POST /api/v1/projects/{project_id}/analyze`

Re-trigger analysis for an existing project. Creates a new analysis record
and job.

**Auth Required:** Yes

**Response (202):**
```json
{
  "message": "Analysis started",
  "job_id": "uuid-v4"
}
```

---

## Analysis Results

### `GET /api/v1/projects/{project_id}/analysis`

Get the latest analysis summary.

**Auth Required:** Yes

**Response (200):**
```json
{
  "id": "uuid-v4",
  "project_id": "uuid-v4",
  "commit_sha": "abc1234def5678",
  "status": "completed",
  "overall_score": 42.5,
  "grade": "C",
  "summary": {
    "total_files_analyzed": 342,
    "total_issues": 47,
    "critical_issues": 5,
    "total_recommendations": 12
  },
  "sub_scores": {
    "code_health": 55.0,
    "dependency_health": 30.0,
    "architecture_quality": 45.0,
    "test_coverage": 20.0,
    "documentation": 60.0,
    "infrastructure_readiness": 50.0,
    "security_posture": 70.0
  },
  "language_breakdown": {"python": 45, "javascript": 12},
  "duration_seconds": 145,
  "started_at": "2026-01-15T12:00:00Z",
  "completed_at": "2026-01-15T12:02:25Z"
}
```

---

### `GET /api/v1/projects/{project_id}/analysis/score`

Get the modernization readiness score breakdown.

**Auth Required:** Yes

**Response (200):**
```json
{
  "overall_score": 42.5,
  "grade": "C",
  "sub_scores": {
    "code_health": 55.0,
    "dependency_health": 30.0,
    "architecture_quality": 45.0,
    "test_coverage": 20.0,
    "documentation": 60.0,
    "infrastructure_readiness": 50.0,
    "security_posture": 70.0
  },
  "priority_areas": [
    {
      "area": "test_coverage",
      "score": 20.0,
      "action": "Add unit tests — 0% coverage detected"
    },
    {
      "area": "dependency_health",
      "score": 30.0,
      "action": "Update 12 outdated packages, fix 3 CVEs"
    },
    {
      "area": "architecture_quality",
      "score": 45.0,
      "action": "Reduce coupling in 5 tightly-coupled modules"
    }
  ]
}
```

---

### `GET /api/v1/projects/{project_id}/analysis/files`

Get file-level metrics (paginated).

**Auth Required:** Yes

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 50 | Max results |
| `risk_level` | string | null | Filter: low/medium/high/critical |
| `language` | string | null | Filter by language |
| `sort_by` | string | complexity | Sort field |
| `sort_order` | string | desc | Sort direction |

**Response (200):**
```json
{
  "files": [
    {
      "file_path": "src/services/payment.py",
      "language": "python",
      "loc": 450,
      "complexity": 28,
      "max_nesting": 6,
      "function_count": 15,
      "class_count": 2,
      "comment_ratio": 0.05,
      "risk_level": "high",
      "issues": [
        {
          "rule": "COMPLEXITY_CRITICAL",
          "severity": "critical",
          "message": "Function process_payment has complexity 28"
        }
      ]
    }
  ],
  "total": 342
}
```

---

### `GET /api/v1/projects/{project_id}/analysis/debt`

Get all technical debt items.

**Auth Required:** Yes

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `severity` | string | Filter: low/medium/high/critical |
| `category` | string | Filter: complexity/style/architecture/security/documentation |

**Response (200):**
```json
{
  "debt_items": [
    {
      "id": "uuid-v4",
      "category": "complexity",
      "severity": "critical",
      "title": "Critical cyclomatic complexity (28)",
      "description": "Function process_payment has 28 independent paths",
      "file_path": "src/services/payment.py",
      "line_start": 45,
      "line_end": 180,
      "suggestion": "Extract payment validation, fee calculation, and notification into separate functions",
      "estimated_hours": 4.0
    }
  ],
  "total": 47,
  "by_severity": {"critical": 5, "high": 12, "medium": 18, "low": 12}
}
```

---

### `GET /api/v1/projects/{project_id}/analysis/dependencies`

Get dependency health findings.

**Auth Required:** Yes

**Response (200):**
```json
{
  "dependencies": [
    {
      "id": "uuid-v4",
      "package_name": "express",
      "current_version": "4.17.1",
      "latest_version": "5.0.1",
      "ecosystem": "npm",
      "days_behind": 890,
      "is_deprecated": false,
      "vulnerability_count": 2,
      "vulnerabilities": [
        {
          "id": "GHSA-xxxx-yyyy",
          "severity": "high",
          "title": "Prototype pollution in qs",
          "fixed_in": "4.19.0"
        }
      ],
      "risk_level": "high",
      "license": "MIT"
    }
  ],
  "total": 45,
  "summary": {
    "total_deps": 45,
    "outdated": 12,
    "deprecated": 1,
    "vulnerable": 3,
    "by_risk": {"critical": 1, "high": 3, "medium": 8, "low": 33}
  }
}
```

---

### `GET /api/v1/projects/{project_id}/analysis/structure`

Get the repository file tree structure.

**Auth Required:** Yes

**Response (200):**
```json
{
  "tree": {
    "name": "legacy-api",
    "type": "directory",
    "children": [
      {
        "name": "src",
        "type": "directory",
        "children": [
          {
            "name": "services",
            "type": "directory",
            "children": [
              {
                "name": "payment.py",
                "type": "file",
                "language": "python",
                "loc": 450,
                "risk_level": "high"
              }
            ]
          }
        ]
      },
      {
        "name": "package.json",
        "type": "file",
        "loc": 35
      }
    ]
  }
}
```

---

## AI Recommendations

### `GET /api/v1/projects/{project_id}/recommendations`

Get all AI-generated modernization recommendations.

**Auth Required:** Yes

**Response (200):**
```json
{
  "recommendations": [
    {
      "id": "uuid-v4",
      "category": "upgrade",
      "priority": "critical",
      "title": "Upgrade Express from v4 to v5",
      "description": "Express 4.x has known vulnerabilities and is approaching end-of-life",
      "rationale": "Express 5 includes security patches, improved async error handling, and better TypeScript support",
      "implementation_steps": "1. Update package.json\\n2. Replace deprecated middleware\\n3. Update error handlers\\n4. Run test suite",
      "estimated_hours": 16.0,
      "impact_score": 9.2,
      "affected_files": ["app.js", "routes/api.js", "middleware/auth.js"],
      "before_code": "app.use(bodyParser.json())",
      "after_code": "app.use(express.json())"
    }
  ],
  "total": 12,
  "by_priority": {"critical": 2, "high": 4, "medium": 4, "low": 2}
}
```

---

### `POST /api/v1/projects/{project_id}/recommendations/{rec_id}/refactor`

Generate AI-powered refactoring code for a specific recommendation.

**Auth Required:** Yes

**Request Body (optional):**
```json
{
  "file_path": "src/services/payment.py",
  "additional_context": "Prefer async/await pattern"
}
```

**Response (200):**
```json
{
  "recommendation_id": "uuid-v4",
  "file_path": "src/services/payment.py",
  "language": "python",
  "before_code": "def process_payment(amount, currency, card, ...):\n    ...",
  "after_code": "async def process_payment(request: PaymentRequest) -> PaymentResult:\n    ...",
  "explanation": "Refactored to use a data class for parameters, async/await for I/O operations, and extracted validation into a separate method."
}
```

---

## Reports

### `GET /api/v1/projects/{project_id}/report`

Get the full modernization report data.

**Auth Required:** Yes

**Response (200):**
```json
{
  "project": { ... },
  "analysis": { ... },
  "score": { ... },
  "debt_summary": { ... },
  "dependency_summary": { ... },
  "recommendations": [ ... ],
  "generated_at": "2026-01-15T12:05:00Z"
}
```

---

### `GET /api/v1/projects/{project_id}/report/export`

Export the report in the specified format.

**Auth Required:** Yes

**Query Parameters:**
| Parameter | Type | Default | Options |
|-----------|------|---------|---------|
| `format` | string | json | json |

**Response:** JSON file download with `Content-Disposition` header.

---

## Jobs

### `GET /api/v1/jobs/{job_id}`

Get the status and progress of a background job.

**Auth Required:** Yes

**Response (200):**
```json
{
  "id": "uuid-v4",
  "project_id": "uuid-v4",
  "job_type": "full_analysis",
  "status": "running",
  "progress": 65,
  "current_step": "Running AI analysis",
  "steps": [
    {"name": "Cloning repository", "status": "completed"},
    {"name": "Scanning files", "status": "completed"},
    {"name": "Parsing source code", "status": "completed"},
    {"name": "Computing metrics", "status": "completed"},
    {"name": "Analyzing dependencies", "status": "completed"},
    {"name": "Running AI analysis", "status": "running"},
    {"name": "Calculating score", "status": "pending"}
  ],
  "started_at": "2026-01-15T12:00:00Z",
  "completed_at": null
}
```

---

## Error Codes

| HTTP Code | Description | Common Causes |
|-----------|-------------|---------------|
| 400 | Bad Request | Invalid input, malformed URL |
| 401 | Unauthorized | Missing or expired token |
| 403 | Forbidden | No access to resource |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource (e.g., repo already added) |
| 422 | Validation Error | Schema validation failure |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |

---

## Rate Limits

| Endpoint Type | Limit |
|--------------|-------|
| Authentication | 10 req/min |
| Read endpoints | 100 req/min |
| Write endpoints | 30 req/min |
| AI endpoints (refactoring) | 10 req/min |

Rate limit headers are included in all responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705312800
```
