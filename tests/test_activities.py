import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)

# Keep a clean copy of initial activities so each test starts from the same state
INITIAL_ACTIVITIES = copy.deepcopy(app_module.activities)

@pytest.fixture(autouse=True)
def reset_activities():
    # Restore the activities dict before each test
    app_module.activities = copy.deepcopy(INITIAL_ACTIVITIES)
    yield


def test_get_activities():
    res = client.get("/activities")
    assert res.status_code == 200
    data = res.json()
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"].get("participants"), list)


def test_signup_new_participant():
    email = "test_student@mergington.edu"
    res = client.post(f"/activities/Chess%20Club/signup?email={email}")
    assert res.status_code == 200
    json_data = res.json()
    assert "Signed up" in json_data.get("message", "")

    # confirm participant was added
    res2 = client.get("/activities")
    assert email in res2.json()["Chess Club"]["participants"]


def test_signup_duplicate_fails():
    email = "dup_student@mergington.edu"
    # first signup should succeed
    r1 = client.post(f"/activities/Chess%20Club/signup?email={email}")
    assert r1.status_code == 200

    # second signup should fail with 400
    r2 = client.post(f"/activities/Chess%20Club/signup?email={email}")
    assert r2.status_code == 400


def test_unregister_participant():
    email = "michael@mergington.edu"  # existing participant from initial data
    r = client.delete(f"/activities/Chess%20Club/participants?email={email}")
    assert r.status_code == 200

    # confirm participant removed
    r2 = client.get("/activities")
    assert email not in r2.json()["Chess Club"]["participants"]
