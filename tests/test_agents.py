def test_create_agent_with_valid_data(test_client, auth_token, test_user_id):
    """
    Test creating an agent with valid data.
    """
    agent_name = "Valid Agent"
    agent_description = "A valid agent for testing."

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
    assert "id" in agent


def test_get_nonexistent_agent(test_client, auth_token):
    """
    Test getting a non-existent agent returns 404.
    """
    nonexistent_id = "nonexistent-agent-id"

    response = test_client.get(
        f"/agents/{nonexistent_id}", headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 404


def test_create_agent_without_auth(test_client):
    """
    Test creating an agent without authentication returns 401.
    """
    agent_name = "Unauthorized Agent"
    agent_description = "This should fail."

    response = test_client.post(
        "/agents",
        json={
            "name": agent_name,
            "description": agent_description,
        },
    )

    # Should return 401 or 422 depending on auth implementation
    assert response.status_code in [401, 422]


def test_agent_lifecycle(test_client, auth_token, test_user_id):
    """
    Test the complete lifecycle of an agent: create, get, verify ownership.
    """
    # Create agent
    agent_name = "Lifecycle Agent"
    agent_description = "Testing agent lifecycle."

    create_response = test_client.post(
        "/agents",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "name": agent_name,
            "description": agent_description,
        },
    )

    assert create_response.status_code == 200
    created_agent = create_response.json()
    agent_id = created_agent["id"]

    # Get agent
    get_response = test_client.get(
        f"/agents/{agent_id}", headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert get_response.status_code == 200
    retrieved_agent = get_response.json()

    # Verify all fields match
    assert retrieved_agent["id"] == agent_id
    assert retrieved_agent["name"] == agent_name
    assert retrieved_agent["description"] == agent_description
    assert retrieved_agent["owner"] == test_user_id
    assert retrieved_agent["owner"] == created_agent["owner"]


def test_multiple_agents_creation(test_client, auth_token, test_user_id):
    """
    Test creating multiple agents for the same user.
    """
    agents_data = [
        {"name": "Agent 1", "description": "First agent"},
        {"name": "Agent 2", "description": "Second agent"},
        {"name": "Agent 3", "description": "Third agent"},
    ]

    created_agents = []

    for agent_data in agents_data:
        response = test_client.post(
            "/agents",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=agent_data,
        )

        assert response.status_code == 200
        agent = response.json()
        assert agent["name"] == agent_data["name"]
        assert agent["description"] == agent_data["description"]
        assert agent["owner"] == test_user_id
        created_agents.append(agent)

    # Verify all agents have different IDs
    agent_ids = [agent["id"] for agent in created_agents]
    assert len(agent_ids) == len(set(agent_ids))  # All IDs should be unique
