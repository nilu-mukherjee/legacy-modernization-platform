"""
Integration tests for the /health endpoint.
"""

from __future__ import annotations

from httpx import AsyncClient


class TestHealthEndpoint:
    async def test_returns_200(self, unauthenticated_client: AsyncClient) -> None:
        response = await unauthenticated_client.get("/health")
        assert response.status_code == 200

    async def test_status_is_healthy(self, unauthenticated_client: AsyncClient) -> None:
        response = await unauthenticated_client.get("/health")
        assert response.json()["status"] == "healthy"

    async def test_version_present(self, unauthenticated_client: AsyncClient) -> None:
        response = await unauthenticated_client.get("/health")
        data = response.json()
        assert "version" in data
        assert data["version"]

    async def test_app_name_present(self, unauthenticated_client: AsyncClient) -> None:
        response = await unauthenticated_client.get("/health")
        assert response.json()["app_name"] == "CodeLens AI"

    async def test_environment_present(self, unauthenticated_client: AsyncClient) -> None:
        response = await unauthenticated_client.get("/health")
        assert "environment" in response.json()

    async def test_content_type_json(self, unauthenticated_client: AsyncClient) -> None:
        response = await unauthenticated_client.get("/health")
        assert "application/json" in response.headers["content-type"]
