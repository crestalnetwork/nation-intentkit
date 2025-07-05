def test_create_and_get_chat(test_client, agent_id_fixture, auth_token, test_user_id):
    """
    Tests that a chat can be created and then retrieved.
    """
    agent_id = agent_id_fixture
    # Create a chat
    response = test_client.post(
        f"/agents/{agent_id}/chats", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    chat = response.json()
    assert chat["agent_id"] == agent_id
    assert chat["user_id"] == test_user_id

    # Get the chat
    chat_id = chat["id"]
    response = test_client.get(
        f"/agents/{agent_id}/chats/{chat_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    retrieved_chat = response.json()
    assert retrieved_chat["id"] == chat_id
    assert retrieved_chat["agent_id"] == agent_id
    assert retrieved_chat["user_id"] == test_user_id

    # Get all chats for the agent
    response = test_client.get(
        f"/agents/{agent_id}/chats", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    chats = response.json()
    assert len(chats) > 0
    assert any(c["id"] == chat_id for c in chats)


def test_update_chat(test_client, agent_id_fixture, auth_token):
    """
    Tests that a chat can be updated.
    """
    agent_id = agent_id_fixture
    response = test_client.post(
        f"/agents/{agent_id}/chats", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    chat = response.json()
    chat_id = chat["id"]

    # Update the chat (currently, the patch endpoint does nothing but return the chat)
    response = test_client.patch(
        f"/agents/{agent_id}/chats/{chat_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"summary": "Updated summary"},  # This field is not actually used yet
    )
    assert response.status_code == 200
    updated_chat = response.json()
    assert updated_chat["id"] == chat_id


def test_delete_chat(test_client, agent_id_fixture, auth_token):
    """
    Tests that a chat can be deleted.
    """
    agent_id = agent_id_fixture
    response = test_client.post(
        f"/agents/{agent_id}/chats", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    chat = response.json()
    chat_id = chat["id"]

    # Delete the chat
    response = test_client.delete(
        f"/agents/{agent_id}/chats/{chat_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 204

    # Try to get the deleted chat
    response = test_client.get(
        f"/agents/{agent_id}/chats/{chat_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 404


def test_retry_message_not_implemented(test_client, agent_id_fixture, auth_token):
    """
    Tests that the retry message endpoint returns 501 Not Implemented.
    """
    agent_id = agent_id_fixture
    chat_id = "test-chat-retry"
    response = test_client.post(
        f"/agents/{agent_id}/chats/{chat_id}/messages/retry",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 501


def test_create_and_get_agent(test_client, auth_token, test_user_id):
    """
    Tests that an agent can be created and then retrieved.
    """
    agent_name = "My Test Agent"
    agent_description = "A test agent for API testing."

    # Create an agent
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
    assert agent["name"] == agent_name
    assert agent["description"] == agent_description
    assert agent["owner"] == test_user_id

    # Get the agent
    agent_id = agent["id"]
    response = test_client.get(
        f"/agents/{agent_id}", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    retrieved_agent = response.json()
    assert retrieved_agent["id"] == agent_id
    assert retrieved_agent["name"] == agent_name
    assert retrieved_agent["description"] == agent_description
    assert retrieved_agent["owner"] == test_user_id


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
