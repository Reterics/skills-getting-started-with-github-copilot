"""Isolated fixtures for the in-memory exercise application."""
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture
def client():
    original = deepcopy(activities)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original)
