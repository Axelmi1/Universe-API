import pytest
from fastapi import status
from app.routers.fit import WorkoutResponse


class TestFitnessGeneration:
    """Test suite for fitness workout generation."""

    @pytest.mark.asyncio
    async def test_workout_generation_success(
        self, async_client, openai_mock_fitness, valid_headers
    ):
        """Test successful workout generation with valid payload."""
        payload = {
            "age": 30,
            "gender": "M",
            "weight": 75.0,
            "height": 180,
            "fitness_level": "intermediate",
            "primary_goal": "muscle_gain",
            "available_equipment": "full_gym",
            "sessions_per_week": 4,
            "session_duration": 60,
            "injuries_limitations": [],
            "experience_years": 2,
        }

        response = await async_client.post(
            "/api/v1/fitness/workout", json=payload, headers=valid_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify required keys are present
        required_keys = ["warmup", "main_workout", "cooldown", "workout_summary"]
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"

        # Verify Pydantic model validation
        WorkoutResponse(**data)

    @pytest.mark.asyncio
    async def test_workout_generation_validation_error_age(
        self, async_client, valid_headers
    ):
        """Test validation error for invalid age."""
        payload = {
            "age": 150,  # Invalid age
            "gender": "F",
            "weight": 60.0,
            "height": 165,
            "fitness_level": "beginner",
            "primary_goal": "weight_loss",
            "available_equipment": "bodyweight",
            "sessions_per_week": 3,
            "session_duration": 45,
        }

        response = await async_client.post(
            "/api/v1/fitness/workout", json=payload, headers=valid_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_workout_generation_validation_error_sessions(
        self, async_client, valid_headers
    ):
        """Test validation error for invalid sessions per week."""
        payload = {
            "age": 25,
            "gender": "M",
            "weight": 80.0,
            "height": 175,
            "fitness_level": "advanced",
            "primary_goal": "strength",
            "available_equipment": "full_gym",
            "sessions_per_week": 15,  # Invalid sessions
            "session_duration": 90,
        }

        response = await async_client.post(
            "/api/v1/fitness/workout", json=payload, headers=valid_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_workout_generation_with_challenges(
        self, async_client, openai_mock_fitness, valid_headers
    ):
        """Test workout generation with specific challenges."""
        payload = {
            "age": 35,
            "gender": "F",
            "weight": 65.0,
            "height": 160,
            "fitness_level": "beginner",
            "primary_goal": "weight_loss",
            "available_equipment": "bodyweight",
            "sessions_per_week": 3,
            "session_duration": 30,
            "injuries_limitations": ["back_pain"],
            "experience_years": 0,
        }

        response = await async_client.post(
            "/api/v1/fitness/workout", json=payload, headers=valid_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        WorkoutResponse(**data)

    @pytest.mark.asyncio
    async def test_workout_generation_advanced_user(
        self, async_client, openai_mock_fitness, valid_headers
    ):
        """Test workout generation for advanced user with specific preferences."""
        payload = {
            "age": 28,
            "gender": "M",
            "weight": 85.0,
            "height": 185,
            "fitness_level": "advanced",
            "primary_goal": "athletic_performance",
            "available_equipment": "full_gym",
            "sessions_per_week": 6,
            "session_duration": 90,
            "experience_years": 5,
        }

        response = await async_client.post(
            "/api/v1/fitness/workout", json=payload, headers=valid_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        WorkoutResponse(**data)

    @pytest.mark.asyncio
    async def test_workout_structure_validation(
        self, async_client, openai_mock_fitness, valid_headers
    ):
        """Test that workout has the correct structure and content."""
        payload = {
            "age": 26,
            "gender": "F",
            "weight": 58.0,
            "height": 168,
            "fitness_level": "intermediate",
            "primary_goal": "general_fitness",
            "available_equipment": "home_basic",
            "sessions_per_week": 4,
            "session_duration": 45,
        }

        response = await async_client.post(
            "/api/v1/fitness/workout", json=payload, headers=valid_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify workout structure
        assert "warmup" in data
        assert "main_workout" in data
        assert "cooldown" in data
        assert "workout_summary" in data

        # Verify each phase has required fields
        for phase_name in ["warmup", "main_workout", "cooldown"]:
            phase = data[phase_name]
            required_fields = ["duration", "exercises", "instructions"]
            for field in required_fields:
                assert field in phase, f"Missing field {field} in {phase_name}"

            # Verify exercises structure
            assert isinstance(phase["exercises"], list)
            assert (
                len(phase["exercises"]) > 0
            ), f"{phase_name} should have at least one exercise"

            for exercise in phase["exercises"]:
                exercise_fields = [
                    "name",
                    "muscle_groups",
                    "sets",
                    "reps",
                    "rest_time",
                    "intensity",
                    "technique_tips",
                ]
                for field in exercise_fields:
                    assert field in exercise, f"Missing field {field} in exercise"

    @pytest.mark.asyncio
    async def test_workout_generation_with_health_conditions(
        self, async_client, openai_mock_fitness, valid_headers
    ):
        """Test workout generation considering health conditions."""
        payload = {
            "age": 45,
            "gender": "M",
            "weight": 90.0,
            "height": 175,
            "fitness_level": "beginner",
            "primary_goal": "weight_loss",
            "available_equipment": "bodyweight",
            "sessions_per_week": 3,
            "session_duration": 30,
            "injuries_limitations": ["knee_problems"],
            "experience_years": 0,
        }

        response = await async_client.post(
            "/api/v1/fitness/workout", json=payload, headers=valid_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        WorkoutResponse(**data)

    @pytest.mark.asyncio
    async def test_workout_generation_missing_api_key(self, async_client):
        """Test workout generation with missing API key."""
        payload = {
            "age": 30,
            "gender": "M",
            "weight": 75.0,
            "height": 180,
            "fitness_level": "intermediate",
            "primary_goal": "muscle_gain",
            "available_equipment": "full_gym",
            "sessions_per_week": 4,
            "session_duration": 60,
        }

        response = await async_client.post("/api/v1/fitness/workout", json=payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_workout_generation_invalid_api_key(self, async_client):
        """Test workout generation with invalid API key."""
        payload = {
            "age": 30,
            "gender": "M",
            "weight": 75.0,
            "height": 180,
            "fitness_level": "intermediate",
            "primary_goal": "muscle_gain",
            "available_equipment": "full_gym",
            "sessions_per_week": 4,
            "session_duration": 60,
        }

        response = await async_client.post(
            "/api/v1/fitness/workout",
            json=payload,
            headers={"X-API-Key": "invalid-key"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestFitnessMetadata:
    """Test suite for fitness metadata endpoints."""

    @pytest.mark.asyncio
    async def test_get_fitness_levels(self, async_client):
        """Test getting fitness levels"""
        response = await async_client.get("/api/v1/metadata/fitness/fitness-levels")

        assert response.status_code == status.HTTP_200_OK
        assert "fitness_levels" in response.json()
        assert len(response.json()["fitness_levels"]) > 0

        # Validate structure of first fitness level
        first_level = response.json()["fitness_levels"][0]
        assert "id" in first_level
        assert "name" in first_level
        assert "description" in first_level

    @pytest.mark.asyncio
    async def test_get_equipment_options(self, async_client):
        """Test getting equipment options"""
        response = await async_client.get("/api/v1/metadata/fitness/equipment")

        assert response.status_code == status.HTTP_200_OK
        assert "equipment_options" in response.json()
        assert len(response.json()["equipment_options"]) > 0

        # Validate structure of first equipment option
        first_option = response.json()["equipment_options"][0]
        assert "id" in first_option
        assert "name" in first_option
        assert "description" in first_option

    @pytest.mark.asyncio
    async def test_get_goals(self, async_client):
        """Test getting fitness goals"""
        response = await async_client.get("/api/v1/metadata/fitness/goals")

        assert response.status_code == status.HTTP_200_OK
        assert "goals" in response.json()
        assert len(response.json()["goals"]) > 0

        # Validate structure of first goal
        first_goal = response.json()["goals"][0]
        assert "id" in first_goal
        assert "name" in first_goal
        assert "description" in first_goal
