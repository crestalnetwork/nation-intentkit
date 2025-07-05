from fastapi.testclient import TestClient
import jwt
import pytest
import os


# Create a test user ID and JWT token
TEST_USER_ID = "test-user"
# Use a known secret for testing, but not the production one
TEST_SECRET = "test-secret"
ALGORITHM = "HS256"

# Create a token and set it as an environment variable for agent_id_fixture
payload = {"sub": TEST_USER_ID}
token = jwt.encode(payload, TEST_SECRET, algorithm=ALGORITHM)

# Set environment variables before importing the app
os.environ["JWT_SECRET"] = TEST_SECRET
os.environ["DB_HOST"] = ""

# Import config and app after setting environment variables
from app.api import app  # noqa: E402


@pytest.fixture(scope="session")
def test_client():
    """Create a test client that will be reused across all test files."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def auth_token():
    """Provide the JWT token for authentication."""
    return token


@pytest.fixture(scope="session")
def test_user_id():
    """Provide the test user ID."""
    return TEST_USER_ID


@pytest.fixture(scope="function")
def agent_id_fixture(test_client, auth_token):
    """Create an agent for each test and yield its ID."""
    agent_name = "Test Agent"
    agent_description = "An agent created for testing."
    response = test_client.post(
        "/agents",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "name": agent_name,
            "description": agent_description,
        },
    )
    assert response.status_code == 200
    agent = response.json()
    yield agent["id"]
