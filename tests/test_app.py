import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Test the /activities endpoint"""

    def test_get_activities(self):
        """Test that activities endpoint returns activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_activities_have_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activities_have_initial_participants(self):
        """Test that activities start with some participants"""
        response = client.get("/activities")
        data = response.json()
        
        assert len(data["Chess Club"]["participants"]) == 2
        assert len(data["Programming Class"]["participants"]) == 2
        assert len(data["Gym Class"]["participants"]) == 2


class TestSignupEndpoint:
    """Test the /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Test successful signup"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant"""
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Programming Class"]["participants"])
        
        # Sign up new participant
        client.post(
            "/activities/Programming%20Class/signup?email=test@mergington.edu"
        )
        
        # Verify participant was added
        response = client.get("/activities")
        new_count = len(response.json()["Programming Class"]["participants"])
        assert new_count == initial_count + 1
        assert "test@mergington.edu" in response.json()["Programming Class"]["participants"]

    def test_signup_nonexistent_activity(self):
        """Test signup for nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUnregisterEndpoint:
    """Test the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregister"""
        # First add a participant
        client.post(
            "/activities/Gym%20Class/signup?email=unregister_test@mergington.edu"
        )
        
        # Then unregister them
        response = client.post(
            "/activities/Gym%20Class/unregister?email=unregister_test@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "remove_test@mergington.edu"
        
        # Add participant
        client.post("/activities/Chess%20Club/signup?email=" + email)
        
        # Verify they were added
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
        # Unregister
        client.post("/activities/Chess%20Club/unregister?email=" + email)
        
        # Verify they were removed
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity(self):
        """Test unregister from nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_nonexistent_participant(self):
        """Test unregister of nonexistent participant returns 404"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirect(self):
        """Test that root endpoint redirects to static HTML"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
