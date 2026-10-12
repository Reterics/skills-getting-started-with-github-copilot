"""Exercise the public HTTP API with Arrange-Act-Assert tests."""
from copy import deepcopy

import pytest

from src.app import activities


def test_root_redirects_to_website(client):
    # Arrange
    path = "/"
    # Act
    response = client.get(path, follow_redirects=False)
    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


@pytest.mark.parametrize("filename", ["index.html", "app.js", "styles.css"])
def test_static_assets_are_served(client, filename):
    # Arrange
    path = f"/static/{filename}"
    # Act
    response = client.get(path)
    # Assert
    assert response.status_code == 200
    assert response.content


def test_list_activities_contains_original_and_six_new_activities(client):
    # Arrange
    expected = {
        "Chess Club", "Programming Class", "Gym Class",
        "Basketball Team", "Swimming Club", "Art Studio",
        "Drama Club", "Debate Team", "Science Club",
    }
    # Act
    response = client.get("/activities")
    # Assert
    assert response.status_code == 200
    assert set(response.json()) == expected
    for activity in response.json().values():
        assert activity["description"]
        assert activity["schedule"]
        assert activity["max_participants"] > 0
        assert isinstance(activity["participants"], list)


def test_signup_is_visible_in_next_activities_request(client):
    # Arrange
    email = "new.student+club@mergington.edu"
    before = len(activities["Chess Club"]["participants"])
    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    updated = client.get("/activities").json()["Chess Club"]["participants"]
    # Assert
    assert response.status_code == 200
    assert email in updated
    assert len(updated) == before + 1


def test_duplicate_signup_is_rejected_without_mutation(client):
    # Arrange
    email = activities["Chess Club"]["participants"][0]
    before = deepcopy(activities)
    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"
    assert activities == before


@pytest.mark.parametrize("method,action", [("post", "signup"), ("delete", "unregister")])
def test_unknown_activity_is_rejected_without_mutation(client, method, action):
    # Arrange
    before = deepcopy(activities)
    # Act
    response = getattr(client, method)(
        f"/activities/Unknown Club/{action}",
        params={"email": "student@mergington.edu"},
    )
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    assert activities == before


def test_unregister_removes_only_selected_participant(client):
    # Arrange
    participants = activities["Chess Club"]["participants"].copy()
    email = participants[0]
    # Act
    response = client.delete(
        "/activities/Chess Club/unregister", params={"email": email}
    )
    updated = client.get("/activities").json()["Chess Club"]["participants"]
    # Assert
    assert response.status_code == 200
    assert updated == participants[1:]


def test_unregister_nonparticipant_is_rejected_without_mutation(client):
    # Arrange
    before = deepcopy(activities)
    # Act
    response = client.delete(
        "/activities/Chess Club/unregister",
        params={"email": "not.registered@mergington.edu"},
    )
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up"
    assert activities == before


def test_student_can_rejoin_after_unregistering(client):
    # Arrange
    email = activities["Chess Club"]["participants"][0]
    # Act
    removed = client.delete("/activities/Chess Club/unregister", params={"email": email})
    registered = client.post("/activities/Chess Club/signup", params={"email": email})
    # Assert
    assert removed.status_code == registered.status_code == 200
    assert activities["Chess Club"]["participants"].count(email) == 1


def test_student_can_join_different_activities(client):
    # Arrange
    email = activities["Chess Club"]["participants"][0]
    # Act
    response = client.post("/activities/Science Club/signup", params={"email": email})
    # Assert
    assert response.status_code == 200
    assert email in activities["Chess Club"]["participants"]
    assert email in activities["Science Club"]["participants"]


@pytest.mark.parametrize("method,action", [("post", "signup"), ("delete", "unregister")])
def test_email_is_required(client, method, action):
    # Arrange
    before = deepcopy(activities)
    # Act
    response = getattr(client, method)(f"/activities/Chess Club/{action}")
    # Assert
    assert response.status_code == 422
    assert activities == before
