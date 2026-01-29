"""Pytest configuration and fixtures."""

import pytest
from hypothesis import settings as hypothesis_settings
from hypothesis import HealthCheck

from ai_cpaas_demo.config.settings import Settings


# Configure Hypothesis for property-based testing
hypothesis_settings.register_profile(
    "default",
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
hypothesis_settings.load_profile("default")


@pytest.fixture
def test_settings():
    """Test configuration settings."""
    return Settings(
        environment="test",
        variant="aws",
        log_level="DEBUG",
        enable_property_tests=True,
    )


@pytest.fixture
def aws_test_settings():
    """AWS variant test settings."""
    return Settings(
        environment="test",
        variant="aws",
        log_level="DEBUG",
    )


@pytest.fixture
def opensource_test_settings():
    """Open source variant test settings."""
    return Settings(
        environment="test",
        variant="opensource",
        log_level="DEBUG",
    )