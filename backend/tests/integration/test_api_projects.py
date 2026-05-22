"""
Integration tests for /api/v1/projects endpoints.

All external dependencies (DB, Redis/ARQ, auth) are overridden via the
``http_client`` and ``unauthenticated_client`` fixtures in conftest.py.
"""

from __future__ import annotations

import uuid

from httpx import AsyncClient


# ── Auth guard ────────────────────────────────────────────────────────────────


class TestProjectsAuthGuard:
    async def test_list_projects_requires_auth(
        self, unauthenticated_client: AsyncClient
    ) -> None:
        response = await unauthenticated_client.get("/api/v1/projects")
        assert response.status_code == 401

    async def test_create_project_requires_auth(
        self, unauthenticated_client: AsyncClient
    ) -> None:
        response = await unauthenticated_client.post(
            "/api/v1/projects",
            json={"repo_url": "https://github.com/owner/repo"},
        )
        assert response.status_code == 401

    async def test_get_project_requires_auth(
        self, unauthenticated_client: AsyncClient
    ) -> None:
        response = await unauthenticated_client.get(
            f"/api/v1/projects/{uuid.uuid4()}"
        )
        assert response.status_code == 401

    async def test_delete_project_requires_auth(
        self, unauthenticated_client: AsyncClient
    ) -> None:
        response = await unauthenticated_client.delete(
            f"/api/v1/projects/{uuid.uuid4()}"
        )
        assert response.status_code == 401


# ── List projects ─────────────────────────────────────────────────────────────


class TestListProjects:
    async def test_returns_200(self, http_client: AsyncClient) -> None:
        response = await http_client.get("/api/v1/projects")
        assert response.status_code == 200

    async def test_response_has_projects_and_total(
        self, http_client: AsyncClient
    ) -> None:
        body = (await http_client.get("/api/v1/projects")).json()
        assert "projects" in body
        assert "total" in body

    async def test_empty_list_when_no_projects(
        self, http_client: AsyncClient
    ) -> None:
        body = (await http_client.get("/api/v1/projects")).json()
        assert body["projects"] == []
        assert body["total"] == 0

    async def test_pagination_params_accepted(self, http_client: AsyncClient) -> None:
        response = await http_client.get("/api/v1/projects?skip=0&limit=10")
        assert response.status_code == 200

    async def test_negative_skip_rejected(self, http_client: AsyncClient) -> None:
        response = await http_client.get("/api/v1/projects?skip=-1")
        assert response.status_code == 422

    async def test_limit_above_100_rejected(self, http_client: AsyncClient) -> None:
        response = await http_client.get("/api/v1/projects?limit=101")
        assert response.status_code == 422


# ── Create project — URL validation ──────────────────────────────────────────


class TestCreateProjectValidation:
    async def test_missing_repo_url_returns_422(
        self, http_client: AsyncClient
    ) -> None:
        response = await http_client.post("/api/v1/projects", json={})
        assert response.status_code == 422

    async def test_non_github_url_returns_400(
        self, http_client: AsyncClient
    ) -> None:
        response = await http_client.post(
            "/api/v1/projects",
            json={"repo_url": "https://gitlab.com/owner/repo"},
        )
        assert response.status_code == 400

    async def test_bare_string_returns_400(self, http_client: AsyncClient) -> None:
        response = await http_client.post(
            "/api/v1/projects",
            json={"repo_url": "owner/repo"},
        )
        assert response.status_code == 400

    async def test_error_detail_field_present(self, http_client: AsyncClient) -> None:
        response = await http_client.post(
            "/api/v1/projects",
            json={"repo_url": "not-a-url"},
        )
        assert response.status_code == 400
        assert "detail" in response.json()

    async def test_valid_github_url_passes_validation(
        self, http_client: AsyncClient
    ) -> None:
        """A well-formed GitHub URL must not return 400 (URL check passed)."""
        response = await http_client.post(
            "/api/v1/projects",
            json={"repo_url": "https://github.com/owner/repo"},
        )
        assert response.status_code != 400


# ── Get / delete — 404 and 422 ───────────────────────────────────────────────


class TestGetProject:
    async def test_nonexistent_project_returns_404(
        self, http_client: AsyncClient
    ) -> None:
        response = await http_client.get(f"/api/v1/projects/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_404_has_detail_field(self, http_client: AsyncClient) -> None:
        response = await http_client.get(f"/api/v1/projects/{uuid.uuid4()}")
        assert "detail" in response.json()

    async def test_invalid_uuid_returns_422(self, http_client: AsyncClient) -> None:
        response = await http_client.get("/api/v1/projects/not-a-uuid")
        assert response.status_code == 422


class TestDeleteProject:
    async def test_nonexistent_project_returns_404(
        self, http_client: AsyncClient
    ) -> None:
        response = await http_client.delete(f"/api/v1/projects/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_invalid_uuid_returns_422(self, http_client: AsyncClient) -> None:
        response = await http_client.delete("/api/v1/projects/not-a-uuid")
        assert response.status_code == 422
