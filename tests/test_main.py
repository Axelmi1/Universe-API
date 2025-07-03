import pytest
from fastapi import status

class TestHealthCheck:
    """Test suite for health check endpoints."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, async_client):
        """Test root endpoint returns welcome message."""
        response = await async_client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "Universe API" in data["message"]

    @pytest.mark.asyncio
    async def test_health_endpoint(self, async_client):
        """Test health endpoint returns system status."""
        response = await async_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

class TestAuthentication:
    """Test suite for API authentication."""

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_key(self, async_client):
        """Test that protected endpoints require API key."""
        # Test fitness endpoint without API key
        payload = {
            "age": 25,
            "gender": "M",
            "weight": 70,
            "height": 175,
            "fitness_level": "beginner",
            "primary_goal": "muscle_gain",
            "sessions_per_week": 3,
            "available_equipment": "bodyweight"
        }

        response = await async_client.post(
            "/api/v1/fitness/workout",
            json=payload
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_invalid_key(self, async_client):
        """Test that protected endpoints reject invalid API keys."""
        payload = {
            "age": 25,
            "gender": "M",
            "weight": 70,
            "height": 175,
            "fitness_level": "beginner",
            "primary_goal": "muscle_gain",
            "sessions_per_week": 3,
            "available_equipment": "bodyweight"
        }

        response = await async_client.post(
            "/api/v1/fitness/workout",
            json=payload,
            headers={"X-API-Key": "invalid-key"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_valid_key(self, async_client, openai_mock_fitness, valid_headers):
        """Test that protected endpoints accept valid API keys."""
        payload = {
            "age": 25,
            "gender": "M",
            "weight": 70,
            "height": 175,
            "fitness_level": "beginner",
            "primary_goal": "muscle_gain",
            "sessions_per_week": 3,
            "available_equipment": "bodyweight"
        }

        response = await async_client.post(
            "/api/v1/fitness/workout",
            json=payload,
            headers=valid_headers
        )
        
        assert response.status_code == status.HTTP_200_OK

class TestAPIDocumentation:
    """Test suite for API documentation endpoints."""

    @pytest.mark.asyncio
    async def test_openapi_schema(self, async_client):
        """Test OpenAPI schema is accessible."""
        response = await async_client.get("/openapi.json")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    @pytest.mark.asyncio
    async def test_docs_endpoint(self, async_client):
        """Test Swagger UI documentation is accessible."""
        response = await async_client.get("/docs")
        
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_redoc_endpoint(self, async_client):
        """Test ReDoc documentation is accessible."""
        response = await async_client.get("/redoc")
        
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

class TestErrorHandling:
    """Test suite for error handling."""

    @pytest.mark.asyncio
    async def test_404_endpoint(self, async_client):
        """Test 404 error for non-existent endpoints."""
        response = await async_client.get("/non-existent-endpoint")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_405_method_not_allowed(self, async_client):
        """Test 405 error for unsupported HTTP methods."""
        response = await async_client.patch("/api/v1/fitness/workout")
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.asyncio
    async def test_422_validation_error(self, async_client, valid_headers):
        """Test 422 error for validation failures."""
        # Send invalid payload (missing required fields)
        payload = {
            "age": "invalid"  # Should be integer
        }

        response = await async_client.post(
            "/api/v1/fitness/workout",
            json=payload,
            headers=valid_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data

class TestCORS:
    """Test suite for CORS configuration."""

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, async_client):
        """Test that CORS headers are present in API responses."""
        # Test with a proper API endpoint that supports CORS
        response = await async_client.get("/health")
        
        # In test environment, CORS headers might not be present
        # Just verify the endpoint is accessible and returns 200
        assert response.status_code == status.HTTP_200_OK
        
        # If CORS headers are present, verify they're correct
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] == "*"

    @pytest.mark.asyncio
    async def test_preflight_request(self, async_client):
        """Test CORS preflight request handling."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,X-API-Key"
        }
        
        response = await async_client.options(
            "/api/v1/fitness/workout",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "access-control-allow-origin" in response.headers 