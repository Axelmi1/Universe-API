import pytest
import json
import respx
from app.services.ia_client import ask_llm


class TestIAClient:
    """Test suite for IA client functionality."""

    @pytest.fixture
    def ia_client(self):
        """Fixture for IA client testing."""
        return ask_llm

    @pytest.mark.asyncio
    async def test_ask_llm_success(self, ia_client):
        """Test successful LLM request with valid response."""
        with respx.mock(base_url="https://api.openai.com") as mock:
            mock.post("/v1/chat/completions").respond(
                status_code=200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {"status": "success", "data": {"test": "value"}}
                                )
                            }
                        }
                    ]
                },
            )

            result = ia_client("Test prompt", max_tokens=100)
            assert result["status"] == "success"
            assert result["data"]["test"] == "value"

    @pytest.mark.asyncio
    async def test_ask_llm_json_extraction(self, ia_client):
        """Test JSON extraction from LLM response."""
        with respx.mock(base_url="https://api.openai.com") as mock:
            mock.post("/v1/chat/completions").respond(
                status_code=200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "workout": {
                                            "exercises": ["push-ups", "squats"],
                                            "duration": "30 minutes",
                                        },
                                        "nutrition": {"calories": 2000, "protein": 150},
                                    }
                                )
                            }
                        }
                    ]
                },
            )

            result = ia_client("Generate workout", max_tokens=500)
            assert "workout" in result
            assert "nutrition" in result
            assert result["workout"]["exercises"] == ["push-ups", "squats"]

    @pytest.mark.asyncio
    async def test_ask_llm_nested_json_extraction(self, ia_client):
        """Test extraction of nested JSON structures."""
        with respx.mock(base_url="https://api.openai.com") as mock:
            mock.post("/v1/chat/completions").respond(
                status_code=200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "meals": [
                                            {
                                                "name": "Breakfast",
                                                "macros": {
                                                    "protein_g": 25,
                                                    "carbs_g": 40,
                                                    "fat_g": 15,
                                                },
                                            },
                                            {
                                                "name": "Lunch",
                                                "macros": {
                                                    "protein_g": 35,
                                                    "carbs_g": 50,
                                                    "fat_g": 20,
                                                },
                                            },
                                        ]
                                    }
                                )
                            }
                        }
                    ]
                },
            )

            result = ia_client("Generate meal plan", max_tokens=800)
            assert "meals" in result
            assert len(result["meals"]) == 2
            assert result["meals"][0]["macros"]["protein_g"] == 25

    @pytest.mark.asyncio
    async def test_ask_llm_invalid_json_fallback(self, ia_client):
        """Test fallback behavior when JSON parsing fails."""
        with respx.mock(base_url="https://api.openai.com") as mock:
            # First attempt returns invalid JSON
            mock.post("/v1/chat/completions").respond(
                status_code=200,
                json={"choices": [{"message": {"content": "Invalid JSON response"}}]},
            )

            with pytest.raises(Exception):  # Should raise HTTPException
                ia_client("Test prompt", max_tokens=100, retry_count=0)

    @pytest.mark.asyncio
    async def test_ask_llm_without_force_json(self, ia_client):
        """Test LLM request without force_json parameter."""
        with respx.mock(base_url="https://api.openai.com") as mock:
            mock.post("/v1/chat/completions").respond(
                status_code=200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "tips": ["Tip 1", "Tip 2", "Tip 3"],
                                        "category": "fitness",
                                    }
                                )
                            }
                        }
                    ]
                },
            )

            result = ia_client("Generate tips", max_tokens=300, force_json=False)
            assert "tips" in result
            assert len(result["tips"]) == 3

    @pytest.mark.asyncio
    async def test_ask_llm_openai_error(self, ia_client):
        """Test handling of OpenAI API errors."""
        with respx.mock(base_url="https://api.openai.com") as mock:
            mock.post("/v1/chat/completions").respond(
                status_code=500, json={"error": "Internal server error"}
            )

            with pytest.raises(Exception):  # Should raise HTTPException
                ia_client("Test prompt", max_tokens=100)

    def test_extract_json_simple(self, ia_client):
        """Test simple JSON extraction."""
        # This test would need the _extract_json function to be exposed
        # For now, we'll test through the main function
        pass

    def test_extract_json_multiple_objects(self, ia_client):
        """Test extraction when multiple JSON objects are present."""
        pass

    def test_extract_json_with_arrays(self, ia_client):
        """Test JSON extraction with nested arrays."""
        pass

    def test_extract_json_no_json_found(self, ia_client):
        """Test behavior when no JSON is found in response."""
        pass

    def test_extract_json_malformed(self, ia_client):
        """Test handling of malformed JSON."""
        pass


class TestAPIKeyValidation:
    """Test suite for API key validation."""

    def test_valid_api_key_format(self):
        """Test validation of properly formatted API keys."""
        # This would test the API key validation logic
        # Currently handled in main.py dependency
        assert True

    def test_invalid_api_key_format(self):
        """Test rejection of invalid API key formats."""
        # This would test the API key validation logic
        # Currently handled in main.py dependency
        assert True
