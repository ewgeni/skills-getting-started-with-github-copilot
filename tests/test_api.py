"""Tests for the Mergington High School API endpoints"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that root path redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that getting activities returns 200 OK"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that activities are returned as a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_activities_contains_expected_activities(self, client):
        """Test that all expected activities are present"""
        response = client.get("/activities")
        data = response.json()
        
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class",
            "Soccer Team", "Swimming Club", "Art Studio",
            "Drama Club", "Debate Team", "Science Olympiad"
        ]
        
        for activity in expected_activities:
            assert activity in data
    
    def test_activity_structure(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds participant to activity"""
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
    
    def test_signup_duplicate_returns_400(self, client):
        """Test that signing up twice returns 400 error"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signing up for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_with_url_encoded_activity(self, client):
        """Test signup with URL-encoded activity name"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_participant_success(self, client):
        """Test successful removal of a participant"""
        # First, add a participant
        email = "toremove@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Then remove them
        response = client.delete(f"/activities/Chess Club/participants/{email}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
    
    def test_remove_participant_actually_removes(self, client):
        """Test that participant is actually removed from activity"""
        # Add participant
        email = "toremove@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Remove participant
        client.delete(f"/activities/Chess Club/participants/{email}")
        
        # Verify removal
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Chess Club"]["participants"]
    
    def test_remove_nonexistent_participant_returns_404(self, client):
        """Test that removing non-existent participant returns 404"""
        response = client.delete(
            "/activities/Chess Club/participants/nonexistent@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_remove_from_nonexistent_activity_returns_404(self, client):
        """Test that removing from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Club/participants/test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_remove_existing_participant(self, client):
        """Test removing a participant that was initially in the activity"""
        # Remove an existing participant
        response = client.delete(
            "/activities/Chess Club/participants/michael@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify removal
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


class TestIntegrationScenarios:
    """Integration tests for common user workflows"""
    
    def test_signup_and_remove_workflow(self, client):
        """Test complete workflow: signup and then remove"""
        email = "workflow@mergington.edu"
        activity = "Drama Club"
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify participant is added
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]
        
        # Remove participant
        remove_response = client.delete(f"/activities/{activity}/participants/{email}")
        assert remove_response.status_code == 200
        
        # Verify participant is removed
        activities = client.get("/activities").json()
        assert email not in activities[activity]["participants"]
    
    def test_multiple_signups_to_different_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "multi@mergington.edu"
        
        # Sign up for multiple activities
        client.post(f"/activities/Chess Club/signup?email={email}")
        client.post(f"/activities/Drama Club/signup?email={email}")
        client.post(f"/activities/Art Studio/signup?email={email}")
        
        # Verify participant is in all activities
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Drama Club"]["participants"]
        assert email in activities["Art Studio"]["participants"]
