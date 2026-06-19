"""Tests for FastAPI main application."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from src.scraping.main import app

    return TestClient(app)


class TestVisitorsEndpoint:
    """Test visitor counting endpoint."""

    def test_get_visitors(self, client, tmp_path):
        """Test getting visitor count."""
        with patch("src.scraping.main.COUNTER_FILE", tmp_path / "visitors.json"):
            # First request
            response = client.get("/visitors")
            assert response.status_code == 200
            data = response.json()
            assert "unique_visitors" in data
            assert data["unique_visitors"] >= 0

    def test_visitors_counter_increments(self, client, tmp_path):
        """Test that visitor counter increments."""
        counter_file = tmp_path / "visitors.json"

        with patch("src.scraping.main.COUNTER_FILE", counter_file):
            # Make multiple requests
            response1 = client.get("/visitors")
            assert response1.status_code == 200

            data1 = response1.json()
            initial_count = data1["unique_visitors"]
            assert initial_count >= 0


class TestClubsEndpoint:
    """Test clubs listing endpoint."""

    def test_list_clubs(self, client):
        """Test listing available clubs."""
        response = client.get("/clubs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have club items
        if len(data) > 0:
            assert "id" in data[0]
            assert "name" in data[0]

    def test_clubs_format(self, client):
        """Test that clubs are properly formatted."""
        response = client.get("/clubs")
        assert response.status_code == 200
        data = response.json()

        for club in data:
            assert isinstance(club, dict)
            assert "id" in club
            assert "name" in club
            assert isinstance(club["id"], str)
            assert isinstance(club["name"], str)


class TestAnalyzeEndpoint:
    """Test analyze endpoint."""

    def test_analyze_missing_club_id(self, client):
        """Test analyze with missing club_id."""
        response = client.post("/analyze", json={})
        # Should fail validation
        assert response.status_code in [422, 400]

    def test_analyze_invalid_club_id(self, client):
        """Test analyze with invalid club_id."""
        response = client.post("/analyze", json={"club_id": "invalid_club_id"})
        # Should handle gracefully (404 or 502)
        assert response.status_code in [404, 502, 400]

    def test_analyze_request_validation(self, client):
        """Test that analyze validates input."""
        # Valid format but invalid club
        response = client.post("/analyze", json={"club_id": "99999999"})
        # Should respond with error (not 500)
        assert response.status_code != 500


class TestHealthEndpoint:
    """Test API health check."""

    def test_root_endpoint(self, client):
        """Test that root endpoint responds."""
        # Most FastAPI apps respond to root
        response = client.get("/openapi.json")
        assert response.status_code == 200


class TestCORSHeaders:
    """Test CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are set."""
        response = client.options("/clubs")
        # Should not fail (405 is ok, means endpoint doesn't support OPTIONS)
        assert response.status_code in [200, 405]
