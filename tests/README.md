# Universe API Test Suite

This directory contains comprehensive tests for the Universe API, covering all endpoints and functionality.

## Test Structure

```
tests/
├── conftest.py          # Test configuration and fixtures
├── test_main.py         # Main API tests (health, auth, docs)
├── test_fitness.py      # Fitness endpoint tests
├── test_nutrition.py    # Nutrition endpoint tests
├── test_tips.py         # Tips endpoint tests
├── test_services.py     # Service layer tests
└── README.md           # This file
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Run only fitness tests
pytest tests/test_fitness.py

# Run only nutrition tests  
pytest tests/test_nutrition.py

# Run only tips tests
pytest tests/test_tips.py

# Run main API tests
pytest tests/test_main.py

# Run service tests
pytest tests/test_services.py
```

### Run Tests with Specific Markers

```bash
# Run unit tests only
pytest -m unit

# Run authentication tests
pytest -m auth

# Run fitness module tests
pytest -m fitness
```

### Test Output Options

```bash
# Verbose output
pytest -v

# Show test coverage
pytest --cov=app

# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Run with detailed failure information
pytest --tb=long

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

## Test Features

### Mocked Dependencies

- **OpenAI API**: All LLM calls are mocked to avoid external dependencies
- **Environment Variables**: Test environment is isolated from production
- **Database**: Uses in-memory/mock database for testing

### Test Categories

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test endpoint interactions and workflows
3. **Authentication Tests**: Verify API key validation and security
4. **Validation Tests**: Test input validation and error handling
5. **Response Tests**: Verify response structure and Pydantic models

### Key Test Scenarios

#### Fitness Tests
- Workout generation with various parameters
- Validation errors for invalid inputs
- Different fitness levels and goals
- Injury limitations and equipment preferences

#### Nutrition Tests
- Meal plan generation with dietary restrictions
- Macro and micronutrient validation
- Hydration guidelines structure
- Budget and time constraints

#### Tips Tests
- Personalized tip generation
- Multiple challenge scenarios
- Health condition considerations
- Tip structure and content validation

#### Service Tests
- IA Client JSON extraction
- Error handling and fallbacks
- API key validation
- OpenAI integration testing

## Test Data

Tests use realistic mock data that matches the expected API responses:

- **Fitness**: Complete workout plans with exercises, sets, and timing
- **Nutrition**: Detailed meal plans with macros and micronutrients  
- **Tips**: Categorized tips for fitness, nutrition, lifestyle, and motivation

## Continuous Integration

The test suite is designed to run in CI/CD environments:

- No external API dependencies (all mocked)
- Fast execution (typically < 30 seconds)
- Comprehensive coverage of all endpoints
- Clear failure reporting and debugging information

## Adding New Tests

When adding new functionality:

1. Add corresponding test cases in the appropriate test file
2. Update fixtures in `conftest.py` if needed
3. Add new markers to `pytest.ini` for categorization
4. Update this README with new test categories

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in your Python path
2. **Async Test Failures**: Make sure `pytest-asyncio` is installed
3. **Mock Issues**: Check that OpenAI mocks are properly configured
4. **Environment Variables**: Verify test environment setup in `conftest.py`

### Debug Mode

Run tests with debugging enabled:
```bash
pytest --pdb  # Drop into debugger on failure
pytest -s     # Show print statements
pytest --lf   # Run only last failed tests
``` 