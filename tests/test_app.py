"""
Tests for the FastAPI application
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app

import pytest

# Import activities for resetting
from app import activities as app_activities

# Create a test client
client = TestClient(app, follow_redirects=False)

# Store original activities for test isolation
ORIGINAL_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Competitive basketball training and games",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 15,
        "participants": ["alex@mergington.edu"]
    },
    "Tennis Club": {
        "description": "Tennis skills development and matches",
        "schedule": "Tuesdays and Saturdays, 3:30 PM - 5:00 PM",
        "max_participants": 10,
        "participants": []
    },
    "Drama Club": {
        "description": "Theater production and acting performances",
        "schedule": "Mondays, Wednesdays, Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 25,
        "participants": ["lucas@mergington.edu", "sarah@mergington.edu"]
    },
    "Art Studio": {
        "description": "Painting, drawing, and sculpture techniques",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 18,
        "participants": ["mia@mergington.edu"]
    },
    "Debate Team": {
        "description": "Competitive debate and public speaking skills",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 16,
        "participants": ["james@mergington.edu", "isabella@mergington.edu"]
    },
    "Science Club": {
        "description": "Explore scientific experiments and research projects",
        "schedule": "Wednesdays, 3:30 PM - 4:45 PM",
        "max_participants": 22,
        "participants": ["noah@mergington.edu"]
    }
}

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the activities dictionary before each test to ensure isolation"""
    app_activities.clear()
    app_activities.update(ORIGINAL_ACTIVITIES.copy())


def test_root_redirect():
    """Test the root endpoint redirects to static/index.html"""
    # Arrange - No special setup needed
    
    # Act
    response = client.get("/")
    
    # Assert
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == "/static/index.html"


def test_get_activities():
    """Test the GET /activities endpoint"""
    # Arrange - Activities are reset by fixture
    
    # Act
    response = client.get("/activities")
    
    # Assert
    assert response.status_code == 200
    
    activities = response.json()
    assert isinstance(activities, dict)
    assert len(activities) == 9
    
    # Check that expected activities exist
    expected_activities = [
        "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
        "Tennis Club", "Drama Club", "Art Studio", "Debate Team", "Science Club"
    ]
    for activity in expected_activities:
        assert activity in activities
    
    # Check structure of one activity
    chess_club = activities["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)


def test_signup_success():
    """Test successful signup for an activity"""
    # Arrange
    email = "test@mergington.edu"
    activity = "Science Club"  # Has 1 participant initially
    
    # Act
    response = client.post(f"/activities/{activity}/signup?email={email}")
    
    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert email in result["message"]
    
    # Additional verification - check participant was added
    response2 = client.get("/activities")
    activities = response2.json()
    assert email in activities[activity]["participants"]


def test_signup_activity_not_found():
    """Test signup for non-existent activity"""
    # Arrange
    email = "test@mergington.edu"
    nonexistent_activity = "NonExistent"
    
    # Act
    response = client.post(f"/activities/{nonexistent_activity}/signup?email={email}")
    
    # Assert
    assert response.status_code == 404
    result = response.json()
    assert result["detail"] == "Activity not found"


def test_signup_already_signed_up():
    """Test signup when student is already signed up"""
    # Arrange
    email = "michael@mergington.edu"
    activity = "Chess Club"  # michael is already signed up
    
    # Act
    response = client.post(f"/activities/{activity}/signup?email={email}")
    
    # Assert
    assert response.status_code == 400
    result = response.json()
    assert "already signed up" in result["detail"]


def test_signup_multiple_students():
    """Test signing up multiple students for the same activity"""
    # Arrange
    activity = "Tennis Club"
    email1 = "student1@mergington.edu"
    email2 = "student2@mergington.edu"
    
    # Act - Sign up first student
    response1 = client.post(f"/activities/{activity}/signup?email={email1}")
    
    # Assert first signup
    assert response1.status_code == 200
    
    # Act - Sign up second student
    response2 = client.post(f"/activities/{activity}/signup?email={email2}")
    
    # Assert second signup
    assert response2.status_code == 200
    
    # Additional verification - check both are in the list
    response3 = client.get("/activities")
    activities = response3.json()
    participants = activities[activity]["participants"]
    assert email1 in participants
    assert email2 in participants
    assert len(participants) == 2


def test_unregister_success():
    """Test successful unregistration from an activity"""
    # Arrange
    email = "michael@mergington.edu"
    activity = "Chess Club"
    
    # Act
    response = client.delete(f"/activities/{activity}/signup?email={email}")
    
    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    
    # Additional verification - check participant was removed
    response2 = client.get("/activities")
    activities = response2.json()
    assert email not in activities[activity]["participants"]


def test_unregister_activity_not_found():
    """Test unregister from non-existent activity"""
    # Arrange
    email = "test@mergington.edu"
    nonexistent_activity = "NonExistent"
    
    # Act
    response = client.delete(f"/activities/{nonexistent_activity}/signup?email={email}")
    
    # Assert
    assert response.status_code == 404
    result = response.json()
    assert result["detail"] == "Activity not found"


def test_unregister_not_signed_up():
    """Test unregister when student is not signed up"""
    # Arrange
    email = "notsignedup@mergington.edu"
    activity = "Chess Club"
    
    # Act
    response = client.delete(f"/activities/{activity}/signup?email={email}")
    
    # Assert
    assert response.status_code == 400
    result = response.json()
    assert "not signed up" in result["detail"]


def test_signup_unregister_cycle():
    """Test signing up, unregistering, then signing up again"""
    # Arrange
    email = "cycle@mergington.edu"
    activity = "Tennis Club"
    
    # Act - Sign up
    response1 = client.post(f"/activities/{activity}/signup?email={email}")
    
    # Assert - Signed up
    assert response1.status_code == 200
    
    # Act - Unregister
    response2 = client.delete(f"/activities/{activity}/signup?email={email}")
    
    # Assert - Unregistered
    assert response2.status_code == 200
    
    # Act - Sign up again
    response3 = client.post(f"/activities/{activity}/signup?email={email}")
    
    # Assert - Signed up again
    assert response3.status_code == 200
    
    # Additional verification - check final state
    response4 = client.get("/activities")
    activities = response4.json()
    assert email in activities[activity]["participants"]