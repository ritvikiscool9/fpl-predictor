# Test Suite Documentation

## Overview
This test suite ensures the reliability and correctness of the FPL Predictor application.

## Test Structure

### `test_predictions.py`
- **Purpose**: Tests core prediction algorithms
- **Coverage**: Player form scoring, fixture analysis, point predictions
- **Key Tests**:
  - Form calculation for different positions
  - Fixture favorability scoring
  - Team strength analysis
  - Injury risk handling

### `test_team_building.py` 
- **Purpose**: Tests team optimization and selection
- **Coverage**: Squad building, budget constraints, formation selection
- **Key Tests**:
  - 15-player squad constraints (2 GK, 5 DEF, 5 MID, 3 FWD)
  - Budget limit enforcement (£100m)
  - Max 3 players per team rule
  - Starting XI formation validation

### `test_data_collection.py`
- **Purpose**: Tests data collection and processing
- **Coverage**: API interactions, data validation, error handling
- **Key Tests**:
  - HTTP request handling
  - Data parsing and validation
  - Database save operations
  - Quality analysis

### `test_database.py`
- **Purpose**: Tests database operations
- **Coverage**: Data population, consistency checks, error recovery
- **Key Tests**:
  - FPL data population
  - Gameweek data handling
  - Missing data scenarios
  - API failure recovery

### `test_api_integration.py`
- **Purpose**: Tests API integration and error scenarios
- **Coverage**: Network errors, timeouts, data validation, performance
- **Key Tests**:
  - API timeout handling
  - Invalid JSON responses
  - Network connectivity issues
  - Large dataset performance

### `conftest.py`
- **Purpose**: Shared test fixtures and utilities
- **Provides**:
  - Sample FPL data
  - Mock match data
  - Player fixtures for all positions
  - Validation helpers

## Running Tests

### Local Testing
```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run specific test file
pytest tests/test_predictions.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run verbose output
pytest -v
```

### CI/CD Testing
Tests run automatically on:
- Push to main branch
- Pull requests
- Manual workflow dispatch

### Test Configuration
- **File**: `pytest.ini`
- **Settings**: Verbose output, short traceback, warnings disabled
- **Coverage**: Aims for >80% code coverage

## Test Data Strategy

### Mocking
- External APIs (FPL, Football-Data.org)
- Database connections (Supabase)
- Network requests
- File system operations

### Fixtures
- Realistic player data samples
- Various match scenarios
- Budget constraint cases
- Error condition simulations

## Quality Checks

### What Tests Cover
✅ **Core Logic**: Prediction algorithms, team building  
✅ **Data Handling**: API responses, database operations  
✅ **Error Scenarios**: Network failures, invalid data  
✅ **Performance**: Large datasets, response times  
✅ **Constraints**: FPL rules, budget limits  

### What Tests Don't Cover (Future Additions)
⏳ **Live API Integration**: Real API endpoint testing  
⏳ **User Interface**: Frontend/CLI interactions  
⏳ **Long-term Data**: Multi-season analysis  
⏳ **ML Model Accuracy**: Prediction quality metrics  

## Best Practices

### Adding New Tests
1. **Follow naming convention**: `test_feature_scenario()`
2. **Use fixtures**: Reuse common test data
3. **Mock external dependencies**: Keep tests isolated
4. **Test edge cases**: Empty data, invalid inputs, errors
5. **Assert meaningful conditions**: Not just "no exception"

### Test Categories
- **Unit Tests**: Individual functions (85% of tests)
- **Integration Tests**: Component interactions (10% of tests)  
- **End-to-End Tests**: Full workflow (5% of tests)

## Debugging Failed Tests

### Common Issues
- **Import errors**: Check PYTHONPATH and module structure
- **Mock issues**: Verify patch paths match actual imports
- **Assertion failures**: Check expected vs actual data formats
- **Timeout errors**: Increase timeouts or mock slower operations

### Debugging Commands
```bash
# Run single test with full output
pytest tests/test_predictions.py::TestPlayerFormScore::test_form_score_zero_games -v -s

# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest --tb=long
```