import pytest
from fastapi import status

from app.routers.nutri import NutritionResponse


class TestNutritionGeneration:
    """Test suite for nutrition plan generation."""

    @pytest.mark.asyncio
    async def test_nutrition_generation_success(
        self, async_client, openai_mock_nutrition, valid_headers
    ):
        """Test successful nutrition plan generation with valid payload."""
        payload = {
            "age": 30,
            "gender": "M",
            "weight": 80.0,
            "height": 180,
            "activity_level": "moderately_active",
            "nutrition_goal": "muscle_gain",
            "dietary_restrictions": [],
            "cooking_time_available": 30,
            "meals_per_day": 3,
        }

        response = await async_client.post(
            "/api/v1/nutrition/plan", json=payload, headers=valid_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify required keys are present
        required_keys = [
            "daily_calories",
            "daily_macros",
            "meals",
            "weekly_meal_prep",
            "shopping_list",
        ]
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"

        # Verify Pydantic model validation
        NutritionResponse(**data)

    @pytest.mark.asyncio
    async def test_nutrition_generation_validation_error_age(
        self, async_client, valid_headers
    ):
        """Test validation error for invalid age."""
        payload = {
            "age": 150,  # Above maximum age
            "gender": "F",
            "weight": 60.0,
            "height": 165,
            "activity_level": "lightly_active",
            "nutrition_goal": "weight_loss",
            "dietary_restrictions": [],
            "cooking_time_available": 15,
            "meals_per_day": 3,
        }

        response = await async_client.post(
            "/api/v1/nutrition/plan", json=payload, headers=valid_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_nutrition_generation_validation_error_weight(
        self, async_client, valid_headers
    ):
        """Test validation error for invalid weight."""
        payload = {
            "age": 25,
            "gender": "M",
            "weight": 500.0,  # Above maximum weight
            "height": 175,
            "activity_level": "very_active",
            "nutrition_goal": "maintenance",
            "dietary_restrictions": [],
            "cooking_time_available": 60,
            "meals_per_day": 3,
        }

        response = await async_client.post(
            "/api/v1/nutrition/plan", json=payload, headers=valid_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_nutrition_generation_with_restrictions(
        self, async_client, openai_mock_nutrition, valid_headers
    ):
        """Test nutrition plan generation with dietary restrictions."""
        payload = {
            "age": 35,
            "gender": "F",
            "weight": 65.0,
            "height": 170,
            "activity_level": "moderately_active",
            "nutrition_goal": "weight_loss",
            "dietary_restrictions": ["vegetarian", "gluten_free"],
            "allergies": ["nuts", "shellfish"],
            "cooking_time_available": 45,
            "meals_per_day": 3,
            "health_conditions": ["diabetes"],
        }

        response = await async_client.post(
            "/api/v1/nutrition/plan", json=payload, headers=valid_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        NutritionResponse(**data)

    @pytest.mark.asyncio
    async def test_nutrition_generation_athlete_profile(
        self, async_client, openai_mock_nutrition, valid_headers
    ):
        """Test nutrition plan generation for athlete profile."""
        payload = {
            "age": 28,
            "gender": "M",
            "weight": 85.0,
            "height": 185,
            "target_weight": 75.0,
            "activity_level": "very_active",
            "nutrition_goal": "weight_loss",
            "dietary_restrictions": [],
            "cooking_time_available": 90,
            "meals_per_day": 4,
        }

        response = await async_client.post(
            "/api/v1/nutrition/plan", json=payload, headers=valid_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        NutritionResponse(**data)

    @pytest.mark.asyncio
    async def test_nutrition_structure_validation(
        self, async_client, openai_mock_nutrition, valid_headers
    ):
        """Test that nutrition plan has the correct structure and content."""
        payload = {
            "age": 32,
            "gender": "F",
            "weight": 70.0,
            "height": 168,
            "activity_level": "lightly_active",
            "nutrition_goal": "maintenance",
            "dietary_restrictions": [],
            "cooking_time_available": 30,
            "meals_per_day": 3,
        }

        response = await async_client.post(
            "/api/v1/nutrition/plan", json=payload, headers=valid_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify nutrition plan structure
        assert "daily_calories" in data
        assert "daily_macros" in data
        assert "meals" in data
        assert "weekly_meal_prep" in data
        assert "shopping_list" in data

        # Verify meals structure
        meals = data["meals"]
        assert isinstance(meals, list)
        assert len(meals) > 0, "Should have at least one meal"

        for meal in meals:
            required_fields = [
                "name",
                "time",
                "calories",
                "macros",
                "ingredients",
                "preparation_time",
                "instructions",
                "tips",
            ]
            for field in required_fields:
                assert field in meal, f"Missing field {field} in meal"

    @pytest.mark.asyncio
    async def test_nutrition_generation_with_health_conditions(
        self, async_client, openai_mock_nutrition, valid_headers
    ):
        """Test nutrition plan generation considering health conditions."""
        payload = {
            "age": 45,
            "gender": "M",
            "weight": 90.0,
            "height": 175,
            "activity_level": "sedentary",
            "nutrition_goal": "weight_loss",
            "dietary_restrictions": [],
            "health_conditions": ["diabetes", "hypertension"],
            "cooking_time_available": 30,
            "meals_per_day": 3,
        }

        response = await async_client.post(
            "/api/v1/nutrition/plan", json=payload, headers=valid_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        NutritionResponse(**data)

    @pytest.mark.asyncio
    async def test_nutrition_generation_missing_api_key(self, async_client):
        """Test nutrition plan generation with missing API key."""
        payload = {
            "age": 30,
            "gender": "M",
            "weight": 80.0,
            "height": 180,
            "activity_level": "moderately_active",
            "nutrition_goal": "muscle_gain",
            "dietary_restrictions": [],
            "cooking_time_available": 30,
            "meals_per_day": 3,
        }

        response = await async_client.post("/api/v1/nutrition/plan", json=payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_nutrition_generation_invalid_api_key(self, async_client):
        """Test nutrition plan generation with invalid API key."""
        payload = {
            "age": 30,
            "gender": "M",
            "weight": 80.0,
            "height": 180,
            "activity_level": "moderately_active",
            "nutrition_goal": "muscle_gain",
            "dietary_restrictions": [],
            "cooking_time_available": 30,
            "meals_per_day": 3,
        }

        response = await async_client.post(
            "/api/v1/nutrition/plan", json=payload, headers={"X-API-Key": "invalid-key"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestNutritionMetadata:
    """Test suite for nutrition metadata endpoints."""

    @pytest.mark.asyncio
    async def test_get_dietary_preferences(self, async_client):
        """Test getting dietary preferences"""
        response = await async_client.get(
            "/api/v1/metadata/nutrition/dietary-preferences"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "dietary_preferences" in response.json()
        assert len(response.json()["dietary_preferences"]) > 0

        # Validate structure of first dietary preference
        first_pref = response.json()["dietary_preferences"][0]
        assert "id" in first_pref
        assert "name" in first_pref
        assert "description" in first_pref

    @pytest.mark.asyncio
    async def test_get_activity_levels(self, async_client):
        """Test getting activity levels"""
        response = await async_client.get("/api/v1/metadata/nutrition/activity-levels")

        assert response.status_code == status.HTTP_200_OK
        assert "activity_levels" in response.json()
        assert len(response.json()["activity_levels"]) > 0

        # Validate structure of first activity level
        first_level = response.json()["activity_levels"][0]
        assert "id" in first_level
        assert "name" in first_level
        assert "description" in first_level

    @pytest.mark.asyncio
    async def test_get_goals(self, async_client):
        """Test getting nutrition goals"""
        response = await async_client.get("/api/v1/metadata/nutrition/goals")

        assert response.status_code == status.HTTP_200_OK
        assert "goals" in response.json()
        assert len(response.json()["goals"]) > 0

        # Validate structure of first goal
        first_goal = response.json()["goals"][0]
        assert "id" in first_goal
        assert "name" in first_goal
        assert "description" in first_goal
