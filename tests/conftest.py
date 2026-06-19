"""Test configuration and fixtures."""

import json
import pytest


@pytest.fixture
def mock_clubs_json(tmp_path):
    """Create a temporary clubs.json file."""
    clubs = {
        "11660020": "Argèles Tennis de Table",
        "11660013": "Bourg Madame TT",
        "11660007": "TT Thuirinois",
    }
    clubs_file = tmp_path / "clubs.json"
    clubs_file.write_text(json.dumps(clubs))
    return clubs_file


@pytest.fixture
def sample_dataframe():
    """Create a sample match dataframe for testing."""
    import pandas as pd

    data = {
        "match_id": [1, 2, 3],
        "player_name": ["Player A", "Player B", "Player C"],
        "home_away": ["home", "away", "home"],
        "result": ["win", "loss", "win"],
        "sets_for": [3, 0, 3],
        "sets_against": [0, 3, 1],
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_fftt_response():
    """Create a mock FFTT API response."""
    return {
        "matches": [
            {
                "date": "2024-01-15",
                "home_team": "Team A",
                "away_team": "Team B",
                "home_score": "3-1",
                "away_score": "1-3",
            }
        ]
    }
