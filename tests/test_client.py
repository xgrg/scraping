"""Tests for client module."""


class TestFFTTClient:
    """Test FFTTClient initialization and methods."""

    def test_client_init(self):
        """Test client initialization."""
        from src.scraping.client import FFTTClient

        client = FFTTClient(cookies={"lid": "test"})
        assert client is not None

    def test_client_config_loading(self, tmp_path):
        """Test loading config file."""
        from src.scraping.client import FFTTClient

        config_file = tmp_path / ".fftt_config"
        client = FFTTClient(config_path=str(config_file))
        assert client is not None

    def test_client_methods_exist(self):
        """Test that client has required methods."""
        from src.scraping.client import FFTTClient

        client = FFTTClient(config_path=None)
        assert hasattr(client, "scrape_club")
        assert callable(getattr(client, "scrape_club"))

    def test_get_clubs_method(self):
        """Test get_clubs method signature."""
        from src.scraping.client import FFTTClient

        client = FFTTClient(config_path=None)
        assert hasattr(client, "get_clubs")
        # get_clubs should take department as parameter
        import inspect

        sig = inspect.signature(client.get_clubs)
        assert "department" in sig.parameters
