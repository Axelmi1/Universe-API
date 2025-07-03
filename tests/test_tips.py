import pytest
from fastapi import status
from app.routers.tips import TipsResponse

class TestTipsGeneration:
    """Test suite for tips generation."""

    @pytest.mark.asyncio
    async def test_tips_generation_success(self, async_client, openai_mock_tips, valid_headers):
        """Test successful tips generation with valid payload."""
        payload = {
            "domain": "fitness",
            "experience_level": "intermediate",
            "format_preference": "quick_tips"
        }

        response = await async_client.post(
            "/api/v1/tips/generate",
            json=payload,
            headers=valid_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify required keys are present
        required_keys = ["tips", "implementation_strategy", "priority_order"]
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"
        
        # Verify Pydantic model validation
        TipsResponse(**data)

    @pytest.mark.asyncio
    async def test_tips_generation_validation_error_age(self, async_client, valid_headers):
        """Test validation error for invalid domain."""
        payload = {
            "domain": "invalid_domain",
            "experience_level": "beginner",
            "format_preference": "quick_tips"
        }

        response = await async_client.post(
            "/api/v1/tips/generate",
            json=payload,
            headers=valid_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_tips_generation_validation_error_time(self, async_client, valid_headers):
        """Test validation error for invalid time constraints."""
        payload = {
            "domain": "fitness",
            "experience_level": "advanced",
            "format_preference": "detailed_guide",
            "time_constraints": 2  # Below minimum time
        }

        response = await async_client.post(
            "/api/v1/tips/generate",
            json=payload,
            headers=valid_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_tips_generation_with_challenges(self, async_client, openai_mock_tips, valid_headers):
        """Test tips generation with specific challenges."""
        payload = {
            "domain": "nutrition",
            "experience_level": "beginner",
            "format_preference": "step_by_step",
            "current_challenges": [
                "lack_of_motivation", 
                "time_constraints", 
                "budget_limitations",
                "lack_of_knowledge"
            ],
            "specific_goals": ["weight_loss", "energy_improvement"],
            "time_constraints": 20
        }

        response = await async_client.post(
            "/api/v1/tips/generate",
            json=payload,
            headers=valid_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        TipsResponse(**data)

    @pytest.mark.asyncio
    async def test_tips_generation_advanced_user(self, async_client, openai_mock_tips, valid_headers):
        """Test tips generation for advanced user with specific preferences."""
        payload = {
            "domain": "fitness",
            "secondary_domains": ["nutrition"],
            "experience_level": "expert",
            "format_preference": "science_based",
            "time_constraints": 90,
            "current_challenges": ["plateau"],
            "specific_goals": ["athletic_performance"],
            "preferred_complexity": "complex"
        }

        response = await async_client.post(
            "/api/v1/tips/generate",
            json=payload,
            headers=valid_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        TipsResponse(**data)

    @pytest.mark.asyncio
    async def test_tips_structure_validation(self, async_client, openai_mock_tips, valid_headers):
        """Test that tips have the correct structure and content."""
        payload = {
            "domain": "mental_health",
            "experience_level": "intermediate",
            "format_preference": "practical_hacks"
        }

        response = await async_client.post(
            "/api/v1/tips/generate",
            json=payload,
            headers=valid_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify tips structure
        assert "tips" in data
        assert len(data["tips"]) >= 3, "Should have at least 3 tips"
        assert len(data["tips"]) <= 5, "Should have at most 5 tips"
        
        # Verify each tip has required fields
        for tip in data["tips"]:
            required_fields = ["title", "category", "difficulty", "time_required", "description", "action_steps", "benefits"]
            for field in required_fields:
                assert field in tip, f"Missing field {field} in tip"
            assert isinstance(tip["action_steps"], list)
            assert isinstance(tip["benefits"], list)

    @pytest.mark.asyncio
    async def test_tips_generation_with_health_conditions(self, async_client, openai_mock_tips, valid_headers):
        """Test tips generation considering lifestyle factors."""
        payload = {
            "domain": "recovery",
            "experience_level": "beginner",
            "format_preference": "detailed_guide",
            "time_constraints": 30,
            "lifestyle_factors": ["busy_schedule", "travel", "stress"],
            "current_challenges": ["lack_of_energy"],
            "age_range": "adult"
        }

        response = await async_client.post(
            "/api/v1/tips/generate",
            json=payload,
            headers=valid_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        TipsResponse(**data)

    @pytest.mark.asyncio
    async def test_tips_generation_missing_api_key(self, async_client):
        """Test tips generation with missing API key."""
        payload = {
            "domain": "fitness",
            "experience_level": "intermediate",
            "format_preference": "quick_tips"
        }

        response = await async_client.post(
            "/api/v1/tips/generate",
            json=payload
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_tips_generation_invalid_api_key(self, async_client):
        """Test tips generation with invalid API key."""
        payload = {
            "domain": "fitness",
            "experience_level": "intermediate",
            "format_preference": "quick_tips"
        }

        response = await async_client.post(
            "/api/v1/tips/generate",
            json=payload,
            headers={"X-API-Key": "invalid-key"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestTipsMetadata:
    """Test suite for tips metadata endpoints."""

    @pytest.mark.asyncio
    async def test_get_fitness_levels(self, async_client):
        """Test getting fitness levels"""
        response = await async_client.get("/api/v1/metadata/tips/fitness-levels")
        
        assert response.status_code == status.HTTP_200_OK
        assert "fitness_levels" in response.json()
        assert len(response.json()["fitness_levels"]) > 0
        
        # Validate structure of first fitness level
        first_level = response.json()["fitness_levels"][0]
        assert "id" in first_level
        assert "name" in first_level
        assert "description" in first_level

    @pytest.mark.asyncio
    async def test_get_challenges(self, async_client):
        """Test getting challenges"""
        response = await async_client.get("/api/v1/metadata/tips/challenges")
        
        assert response.status_code == status.HTTP_200_OK
        assert "challenges" in response.json()
        assert len(response.json()["challenges"]) > 0
        
        # Validate structure of first challenge
        first_challenge = response.json()["challenges"][0]
        assert "id" in first_challenge
        assert "name" in first_challenge
        assert "description" in first_challenge

    @pytest.mark.asyncio
    async def test_get_preferred_activities(self, async_client):
        """Test getting preferred activities"""
        response = await async_client.get("/api/v1/metadata/tips/activities")
        
        assert response.status_code == status.HTTP_200_OK
        assert "activities" in response.json()
        assert len(response.json()["activities"]) > 0
        
        # Validate structure of first activity
        first_activity = response.json()["activities"][0]
        assert "id" in first_activity
        assert "name" in first_activity
        assert "description" in first_activity

    @pytest.mark.asyncio
    async def test_get_health_conditions(self, async_client):
        """Test getting health conditions"""
        response = await async_client.get("/api/v1/metadata/tips/health-conditions")
        
        assert response.status_code == status.HTTP_200_OK
        assert "health_conditions" in response.json()
        assert len(response.json()["health_conditions"]) > 0
        
        # Validate structure of first health condition
        first_condition = response.json()["health_conditions"][0]
        assert "id" in first_condition
        assert "name" in first_condition
        assert "description" in first_condition 