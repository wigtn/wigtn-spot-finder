"""
Integration tests for API endpoints.
Tests the FastAPI application with mock dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


# Note: These tests require the API to be importable
# Run with: pytest tests/integration/test_api.py -v


@pytest.fixture
def client():
    """Create a test client for the API."""
    from src.api.main import app

    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_endpoint(self, client):
        """Test /health endpoint returns 200."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "description" in data


class TestChatEndpoints:
    """Test chat API endpoints."""

    @patch("src.api.routes.chat.create_business_agent")
    def test_chat_endpoint_basic(self, mock_agent_factory, client):
        """Test basic chat endpoint."""
        # Setup mock
        mock_agent = AsyncMock()
        mock_agent.invoke.return_value = {
            "response": "Hello! I can help you explore Korea.",
            "messages": [],
            "thread_id": "test_thread",
        }
        mock_agent_factory.return_value = mock_agent

        # Make request
        response = client.post(
            "/api/v1/chat",
            json={
                "message": "Hello, I want to visit Seoul",
                "language": "en",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "thread_id" in data
        assert data["response"] == "Hello! I can help you explore Korea."

    @patch("src.api.routes.chat.create_business_agent")
    def test_chat_endpoint_with_thread_id(self, mock_agent_factory, client):
        """Test chat endpoint with existing thread_id."""
        mock_agent = AsyncMock()
        mock_agent.invoke.return_value = {
            "response": "Sure, let me help with that.",
            "messages": [],
            "thread_id": "existing_thread_123",
        }
        mock_agent_factory.return_value = mock_agent

        response = client.post(
            "/api/v1/chat",
            json={
                "message": "What's good to eat there?",
                "thread_id": "existing_thread_123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == "existing_thread_123"

    def test_chat_endpoint_empty_message_rejected(self, client):
        """Test that empty messages are rejected."""
        response = client.post(
            "/api/v1/chat",
            json={"message": ""},
        )

        assert response.status_code == 422  # Validation error

    def test_chat_endpoint_message_too_long_rejected(self, client):
        """Test that overly long messages are rejected."""
        response = client.post(
            "/api/v1/chat",
            json={"message": "a" * 5000},  # Exceeds max_length
        )

        assert response.status_code == 422  # Validation error


class TestConversationEndpoints:
    """Test conversation management endpoints."""

    @patch("src.api.routes.chat.create_business_agent")
    def test_list_conversations(self, mock_agent_factory, client):
        """Test listing conversations."""
        # First create a conversation
        mock_agent = AsyncMock()
        mock_agent.invoke.return_value = {
            "response": "Hello!",
            "messages": [],
            "thread_id": "test_thread",
        }
        mock_agent_factory.return_value = mock_agent

        client.post("/api/v1/chat", json={"message": "Hi"})

        # List conversations
        response = client.get("/api/v1/conversations")

        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert "total" in data

    @patch("src.api.routes.chat.create_business_agent")
    def test_get_conversation_not_found(self, mock_agent_factory, client):
        """Test getting non-existent conversation."""
        response = client.get("/api/v1/conversations/nonexistent_thread")

        assert response.status_code == 404

    @patch("src.api.routes.chat.create_business_agent")
    def test_delete_conversation(self, mock_agent_factory, client):
        """Test deleting a conversation."""
        # First create a conversation
        mock_agent = AsyncMock()
        mock_agent.invoke.return_value = {
            "response": "Hello!",
            "messages": [],
            "thread_id": "delete_test_thread",
        }
        mock_agent_factory.return_value = mock_agent

        client.post(
            "/api/v1/chat",
            json={"message": "Hi", "thread_id": "delete_test_thread"},
        )

        # Delete it
        response = client.delete("/api/v1/conversations/delete_test_thread")

        assert response.status_code == 200

        # Verify it's gone
        response = client.get("/api/v1/conversations/delete_test_thread")
        assert response.status_code == 404


class TestCORSHeaders:
    """Test CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present."""
        response = client.options(
            "/api/v1/chat",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )

        # In development mode, should allow all origins
        assert "access-control-allow-origin" in response.headers
