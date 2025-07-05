from fastapi.testclient import TestClient
import jwt
from app.config import config
from unittest.mock import AsyncMock, patch
import pytest


# Create a test user ID and JWT token
TEST_USER_ID = "test-user"
# Use a known secret for testing, but not the production one
TEST_SECRET = "test-secret"
ALGORITHM = "HS256"

# Create a token and set it as an environment variable for agent_id_fixture
payload = {"aud": TEST_USER_ID}
token = jwt.encode(payload, TEST_SECRET, algorithm=ALGORITHM)

# fix config
config.db["host"] = ""
config.jwt_secret = TEST_SECRET


try:
    from app.api import app
except ImportError:
    raise ImportError("app.api is not imported")


@pytest.fixture(scope="session")
def test_client():
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def agent_id_fixture(test_client):
    """Create an agent once for the session and yield its ID."""
    agent_name = "Session Agent"
    agent_description = "An agent created for the test session."
    response = test_client.post(
        "/agents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": agent_name,
            "description": agent_description,
        },
    )
    assert response.status_code == 200
    agent = response.json()
    yield agent["id"]


def test_create_and_get_chat(test_client, agent_id_fixture):
    """
    Tests that a chat can be created and then retrieved.
    """
    agent_id = agent_id_fixture
    # Create a chat
    response = test_client.post(
        f"/agents/{agent_id}/chats", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    chat = response.json()
    assert chat["agent_id"] == agent_id
    assert chat["user_id"] == TEST_USER_ID

    # Get the chat
    chat_id = chat["id"]
    response = test_client.get(
        f"/agents/{agent_id}/chats/{chat_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    retrieved_chat = response.json()
    assert retrieved_chat["id"] == chat_id
    assert retrieved_chat["agent_id"] == agent_id
    assert retrieved_chat["user_id"] == TEST_USER_ID

    # Get all chats for the agent
    response = test_client.get(
        f"/agents/{agent_id}/chats", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    chats = response.json()
    assert len(chats) > 0
    assert any(c["id"] == chat_id for c in chats)


def test_update_chat(test_client, agent_id_fixture: str):
    """
    Tests that a chat can be updated.
    """
    agent_id = agent_id_fixture
    response = test_client.post(
        f"/agents/{agent_id}/chats", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    chat = response.json()
    chat_id = chat["id"]

    # Update the chat (currently, the patch endpoint does nothing but return the chat)
    response = test_client.patch(
        f"/agents/{agent_id}/chats/{chat_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"summary": "Updated summary"},  # This field is not actually used yet
    )
    assert response.status_code == 200
    updated_chat = response.json()
    assert updated_chat["id"] == chat_id


def test_delete_chat(test_client, agent_id_fixture: str):
    """
    Tests that a chat can be deleted.
    """
    agent_id = agent_id_fixture
    response = test_client.post(
        f"/agents/{agent_id}/chats", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    chat = response.json()
    chat_id = chat["id"]

    # Delete the chat
    response = test_client.delete(
        f"/agents/{agent_id}/chats/{chat_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    # Try to get the deleted chat
    response = test_client.get(
        f"/agents/{agent_id}/chats/{chat_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_send_and_get_message(test_client, agent_id_fixture: str):
    """
    Tests that a message can be sent and then retrieved.
    """
    agent_id = agent_id_fixture
    # Mock Agent.get to return a dummy agent
    with patch(
        "intentkit.models.agent.Agent.get", new_callable=AsyncMock
    ) as mock_get_agent:
        mock_get_agent.return_value = AsyncMock(id=agent_id, name="Test Agent")

        response = test_client.post(
            f"/agents/{agent_id}/chats", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        chat = response.json()
        chat_id = chat["id"]

        # Send a message
        message_content = "Hello, agent!"
        response = test_client.post(
            f"/agents/{agent_id}/chats/{chat_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": TEST_USER_ID,
                "message": message_content,
                "stream": False,
            },
        )
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) > 0
        assert messages[0]["message"] == message_content

        # Get all messages for the chat
        response = test_client.get(
            f"/agents/{agent_id}/chats/{chat_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        retrieved_messages = response.json()
        assert len(retrieved_messages) > 0
        assert retrieved_messages[0]["message"] == message_content

        # Get a specific message
        message_id = retrieved_messages[0]["id"]
        response = test_client.get(
            f"/messages/{message_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        retrieved_message = response.json()
        assert retrieved_message["id"] == message_id
        assert retrieved_message["message"] == message_content


def test_retry_message_not_implemented(test_client, agent_id_fixture: str):
    """
    Tests that the retry message endpoint returns 501 Not Implemented.
    """
    agent_id = agent_id_fixture
    chat_id = "test-chat-retry"
    response = test_client.post(
        f"/agents/{agent_id}/chats/{chat_id}/messages/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 501


def test_create_and_get_agent(test_client, agent_id_fixture: str):
    """
    Tests that an agent can be created and then retrieved.
    """
    agent_name = "My Test Agent"
    agent_description = "A test agent for API testing."

    # Create an agent
    response = test_client.post(
        "/agents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": agent_name,
            "description": agent_description,
        },
    )
    assert response.status_code == 200
    agent = response.json()
    assert agent["name"] == agent_name
    assert agent["description"] == agent_description
    assert agent["owner_id"] == TEST_USER_ID

    # Get the agent
    agent_id = agent["id"]
    response = test_client.get(
        f"/agents/{agent_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    retrieved_agent = response.json()
    assert retrieved_agent["id"] == agent_id
    assert retrieved_agent["name"] == agent_name
    assert retrieved_agent["description"] == agent_description
    assert retrieved_agent["owner_id"] == TEST_USER_ID


def test_health_endpoint(test_client):
    """
    Tests that the health endpoint returns the correct status.
    """
    response = test_client.get("/health")
    assert response.status_code == 200
    health_data = response.json()
    assert health_data["status"] == "healthy"
    assert health_data["service"] == "Nation IntentKit API"
    assert "version" in health_data
