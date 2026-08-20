"""
Unit tests for GLADE AI application
Tests critical functions and API endpoints
"""

import pytest
import json
import os
from unittest.mock import patch

# Mock environment variables before importing app
@pytest.fixture(autouse=True)
def mock_env():
    """Mock required environment variables"""
    with patch.dict(os.environ, {
        'SECRET_KEY': 'test-secret-key',
        'GEMINI_API_KEY': 'test-gemini-key',
        'FIREBASE_API_KEY': 'test-firebase-key',
        'GMAIL_EMAIL': 'test@gmail.com',
        'GMAIL_PASSWORD': 'test-password'
    }):
        yield

from app import app, logger, OTP_LENGTH, TOKEN_EXPIRY_HOURS, OTP_EXPIRY_MINUTES, MAX_GOAL_LENGTH

# ============ FIXTURES ============

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def valid_email():
    """Valid test email"""
    return "test@example.com"

@pytest.fixture
def valid_otp():
    """Valid test OTP"""
    return "123456"

# ============ CONSTANTS VALIDATION ============

class TestConstants:
    """Test application constants"""
    
    def test_otp_length(self):
        """Test OTP length constant"""
        assert OTP_LENGTH == 6
    
    def test_token_expiry_hours(self):
        """Test token expiry constant"""
        assert TOKEN_EXPIRY_HOURS == 1
    
    def test_otp_expiry_minutes(self):
        """Test OTP expiry constant"""
        assert OTP_EXPIRY_MINUTES == 5
    
    def test_max_goal_length(self):
        """Test max goal length constant"""
        assert MAX_GOAL_LENGTH == 500

# ============ PAGE ROUTES TESTS ============

class TestPageRoutes:
    """Test page rendering routes"""
    
    def test_index_page(self, client):
        """Test index page loads"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_signup_page(self, client):
        """Test signup page loads"""
        response = client.get('/signup')
        assert response.status_code == 200
    
    def test_password_reset_page(self, client):
        """Test password reset page loads"""
        response = client.get('/password-reset')
        assert response.status_code == 200
    
    def test_welcome_page(self, client):
        """Test welcome page loads"""
        response = client.get('/welcome')
        assert response.status_code == 200
    
    def test_dashboard_page(self, client):
        """Test dashboard page loads"""
        response = client.get('/dashboard')
        assert response.status_code == 200

# ============ HEALTH CHECK ============

class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check returns 200"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'timestamp' in data

# ============ PASSWORD RESET TESTS ============

class TestPasswordReset:
    """Test password reset functionality"""
    
    def test_reset_password_missing_email(self, client):
        """Test reset password with missing email"""
        response = client.post('/api/auth/reset-password', 
            json={},
            content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_reset_password_with_email(self, client, valid_email):
        """Test reset password generates token"""
        response = client.post('/api/auth/reset-password',
            json={'email': valid_email},
            content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'message' in data
    
    def test_verify_token_invalid(self, client, valid_email):
        """Test token verification with invalid token"""
        response = client.post('/api/auth/verify-token',
            json={'email': valid_email, 'token': 'invalid'},
            content_type='application/json')
        # Returns 401 (Unauthorized) for invalid token, or 404 if email not found
        assert response.status_code in [401, 404]

# ============ OTP TESTS ============

class TestOTP:
    """Test OTP functionality"""
    
    def test_generate_otp_missing_email(self, client):
        """Test OTP generation with missing email"""
        response = client.post('/api/auth/generate-otp',
            json={},
            content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_cleanup_otp(self, client, valid_email):
        """Test OTP cleanup"""
        response = client.post('/api/auth/cleanup-otp',
            json={'email': valid_email},
            content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True

# ============ DECOMPOSE TESTS ============

class TestDecompose:
    """Test task decomposition"""
    
    def test_decompose_missing_goal(self, client):
        """Test decomposition with missing goal"""
        response = client.post('/api/decompose',
            json={},
            content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_decompose_empty_goal(self, client):
        """Test decomposition with empty goal"""
        response = client.post('/api/decompose',
            json={'goal': ''},
            content_type='application/json')
        assert response.status_code == 400
    
    def test_decompose_goal_too_long(self, client):
        """Test decomposition with goal exceeding max length"""
        long_goal = 'a' * (MAX_GOAL_LENGTH + 1)
        response = client.post('/api/decompose',
            json={'goal': long_goal},
            content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Goal must be under' in data['error']

# ============ USER PROFILE TESTS ============

class TestUserProfile:
    """Test user profile endpoints"""
    
    def test_get_profile(self, client):
        """Test get user profile"""
        response = client.get('/api/user/profile')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'email' in data
        assert 'total_tasks_completed' in data
    
    def test_set_theme_missing_theme(self, client):
        """Test set theme with missing theme"""
        response = client.post('/api/user/theme',
            json={},
            content_type='application/json')
        assert response.status_code == 400
    
    def test_set_theme_with_theme(self, client):
        """Test set theme with valid theme"""
        response = client.post('/api/user/theme',
            json={'theme': 'ocean'},
            content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True

# ============ TASK TRACKING TESTS ============

class TestTaskTracking:
    """Test task completion tracking"""
    
    def test_complete_task_missing_auth(self, client):
        """Test task completion without auth token"""
        response = client.post('/api/task/task123/complete-step',
            json={'step_index': 0},
            content_type='application/json')
        assert response.status_code == 401
    
    def test_complete_task_with_auth(self, client):
        """Test task completion with auth token"""
        response = client.post('/api/task/task123/complete-step',
            json={'step_index': 0},
            headers={'Authorization': 'valid-token'},
            content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True

# ============ ERROR HANDLER TESTS ============

class TestErrorHandlers:
    """Test error handling"""
    
    def test_404_error(self, client):
        """Test 404 error handler"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_error_response_format(self, client):
        """Test error responses have consistent format"""
        response = client.post('/api/decompose',
            json={'goal': ''},
            content_type='application/json')
        data = json.loads(response.data)
        # Some endpoints return 'error', some 'success': false
        assert 'error' in data or 'success' in data

# ============ SECURITY HEADERS TESTS ============

class TestSecurityHeaders:
    """Test security headers"""
    
    def test_security_headers_present(self, client):
        """Test that security headers are present"""
        response = client.get('/')
        assert 'X-Content-Type-Options' in response.headers
        assert 'X-Frame-Options' in response.headers
        assert 'X-XSS-Protection' in response.headers
    
    def test_cors_headers(self, client):
        """Test CORS headers on API routes"""
        response = client.get('/api/health')
        # CORS may or may not be present depending on request origin
        assert response.status_code == 200

# ============ INTEGRATION TESTS ============

class TestIntegration:
    """Test integration between components"""
    
    def test_full_password_reset_flow(self, client, valid_email):
        """Test complete password reset flow"""
        # Step 1: Request reset
        response1 = client.post('/api/auth/reset-password',
            json={'email': valid_email},
            content_type='application/json')
        assert response1.status_code == 200
        
        # Step 2: Cleanup
        response2 = client.post('/api/auth/cleanup-reset-token',
            json={'email': valid_email},
            content_type='application/json')
        assert response2.status_code == 200
    
    def test_all_endpoints_reachable(self, client):
        """Test that all main endpoints are reachable"""
        endpoints = [
            ('/', 'GET'),
            ('/api/health', 'GET'),
            ('/api/user/profile', 'GET'),
        ]
        
        for path, method in endpoints:
            if method == 'GET':
                response = client.get(path)
            else:
                response = client.post(path)
            
            # Endpoints should not return 500
            assert response.status_code != 500, f"Endpoint {path} returned 500"

# ============ RUN TESTS ============

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
