from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_available_activities():
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activities


def test_signup_adds_participant():
    response = client.post(
        "/activities/Soccer Team/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up student@mergington.edu for Soccer Team"
    }
    assert "student@mergington.edu" in activities["Soccer Team"]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email", "expected_status", "expected_detail"),
    [
        (
            "Chess Club",
            "michael@mergington.edu",
            400,
            "Student is already signed up for this activity",
        ),
        (
            "Unknown Activity",
            "student@mergington.edu",
            404,
            "Activity not found",
        ),
    ],
)
def test_signup_rejects_invalid_request(
    activity_name, email, expected_status, expected_detail
):
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}


def test_unregister_removes_participant():
    response = client.delete(
        "/activities/Chess Club/unregister",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered michael@mergington.edu from Chess Club"
    }
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_signup_delete_alias_unregisters_participant():
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 200
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email", "expected_status", "expected_detail"),
    [
        (
            "Chess Club",
            "student@mergington.edu",
            400,
            "Student is not signed up for this activity",
        ),
        (
            "Unknown Activity",
            "student@mergington.edu",
            404,
            "Activity not found",
        ),
    ],
)
def test_unregister_rejects_invalid_request(
    activity_name, email, expected_status, expected_detail
):
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
