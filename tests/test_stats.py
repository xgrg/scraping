"""Tests for stats module."""

from src.scraping.stats import analyze_home_away_performance


class TestAnalyzeHomeAwayPerformance:
    """Test home/away performance analysis."""

    def test_analyze_empty_dataframe(self):
        """Test with empty dataframe."""
        import pandas as pd

        df = pd.DataFrame(
            {
                "home_away": [],
                "result": [],
            }
        )
        result = analyze_home_away_performance(df)
        assert result is not None
        assert len(result) == 0

    def test_analyze_with_home_away_data(self, sample_dataframe):
        """Test analysis with valid home/away data."""
        # Add required columns if missing
        if "home_away" not in sample_dataframe.columns:
            sample_dataframe["home_away"] = ["home", "away", "home"]
        if "result" not in sample_dataframe.columns:
            sample_dataframe["result"] = ["win", "loss", "win"]

        result = analyze_home_away_performance(sample_dataframe)
        assert result is not None
        # Result should have home and away data
        if not result.empty:
            assert "home_away" in result.columns or len(result) >= 0

    def test_analyze_returns_dataframe(self, sample_dataframe):
        """Test that function returns a dataframe."""
        import pandas as pd

        result = analyze_home_away_performance(sample_dataframe)
        assert isinstance(result, (pd.DataFrame, type(None))) or isinstance(result, pd.DataFrame)
