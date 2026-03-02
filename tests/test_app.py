import copy
import pytest
from fastapi.testclient import TestClient

from src import app


@pytest.fixture
def client():
    return TestClient(app.app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Ensure the global `activities` dict is reset between tests."""
    original = copy.deepcopy(app.activities)
    yield
    app.activities.clear()
    app.activities.update(original)


def test_get_activities_returns_all(client):
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    # there are a known number of activities in the default dataset
    assert "Chess Club" in data
    assert isinstance(data, dict)


def test_signup_success(client):
    resp = client.post("/activities/Chess%20Club/signup?email=test@example.com")
    assert resp.status_code == 200
    assert "Signed up" in resp.json()["message"]

    # verify participant list updated
    get = client.get("/activities")
    assert "test@example.com" in get.json()["Chess Club"]["participants"]


def test_signup_duplicate_fails(client):
    # initial data already contains michael@mergington.edu
    resp = client.post("/activities/Chess%20Club/signup?email=michael@mergington.edu")
    assert resp.status_code == 400
    assert "already signed up" in resp.json()["detail"]


def test_signup_nonexistent_activity(client):
    resp = client.post("/activities/Nope/signup?email=a@b.com")
    assert resp.status_code == 404


def test_unregister_success(client):
    # remove existing participant
    resp = client.delete("/activities/Chess%20Club/signup?email=michael@mergington.edu")
    assert resp.status_code == 200
    assert "Removed" in resp.json()["message"]


def test_unregister_not_registered(client):
    resp = client.delete("/activities/Chess%20Club/signup?email=not@there.com")
    assert resp.status_code == 404


def test_signup_full_fails(client):
    # set max_participants to current length and try signup
    club = app.activities["Chess Club"]
    club["max_participants"] = len(club["participants"])
    resp = client.post("/activities/Chess%20Club/signup?email=new@user.com")
    assert resp.status_code == 400
    assert "full" in resp.json()["detail"]
