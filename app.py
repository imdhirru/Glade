from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from google import genai
from google.genai import types
import os
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import secrets
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

load_dotenv()

# ============ LOGGING CONFIGURATION ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ ENVIRONMENT VALIDATION ============
def validate_environment():
    """Validate required environment variables on startup"""
    required_vars = ['SECRET_KEY', 'GEMINI_API_KEY', 'FIREBASE_API_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")
    
    logger.info("✅ All required environment variables configured")

# Validate on startup
try:
    validate_environment()
except ValueError as e:
    logger.error(f"Startup failed: {e}")
    raise

# ============ CONSTANTS ============
OTP_LENGTH = 6
TOKEN_EXPIRY_HOURS = 1
OTP_EXPIRY_MINUTES = 5
MAX_GOAL_LENGTH = 500
RATE_LIMIT_OTP = "5 per minute"
RATE_LIMIT_RESET = "3 per minute"
RATE_LIMIT_DECOMPOSE = "20 per minute"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Enable CORS for all routes
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# ============ SECURITY HEADERS ============
@app.after_request
def set_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' fonts.googleapis.com; font-src fonts.gstatic.com"
    return response

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are an expert executive function coach for someone with ADHD/Autism. 
Your goal is to break down a scary, vague task into tiny, non-threatening "Micro-Wins".
RULES:
1. Output ONLY a valid JSON list of strings. No extra text.
2. Each step must take less than 10 minutes to do.
3. The first step must be laughably easy (e.g., "Stand up").
Example Input: "Clean my room"
Example Output: ["Put on your favorite song", "Pick up all trash on the floor", "Put dirty clothes in hamper", "Make the bed", "High five yourself"]
"""

MODEL_NAME = "gemini-flash-latest"

# In-memory storage for password reset tokens
reset_tokens = {}

# In-memory OTP storage
otp_storage = {}

# Gmail configuration
GMAIL_EMAIL = os.getenv('GMAIL_EMAIL')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')

# Firebase configuration
FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')

def send_reset_email(to_email, token):
    """
    Send password reset email via Gmail
    """
    try:
        if not GMAIL_EMAIL or not GMAIL_PASSWORD:
            logger.warning("Gmail credentials not configured. Skipping email send.")
            logger.info(f"Reset Token (for manual testing): {token[:20]}...")
            return True

        # Create email
        subject = "🔐 Smart Companion - Reset Your Password"
        
        app_url = os.getenv('APP_URL', 'http://localhost:5000')
        reset_link = f"{app_url}/password-reset?token={token}&email={to_email}"
        
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #667eea;">Password Reset Request</h2>
                    
                    <p>Hi,</p>
                    
                    <p>We received a request to reset your password. Click the button below to proceed:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" style="background-color: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                            Reset Password
                        </a>
                    </div>
                    
                    <p>Or copy this code and enter it on the reset page:</p>
                    <div style="background: #f0f0f0; padding: 15px; border-radius: 5px; text-align: center; font-family: monospace; font-size: 18px; letter-spacing: 2px; margin: 20px 0;">
                        <strong>{token}</strong>
                    </div>
                    
                    <p style="color: #999; font-size: 12px;">
                        ⏰ This link expires in 1 hour.<br>
                        If you didn't request this, please ignore this email.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="text-align: center; color: #999; font-size: 12px;">
                        Smart Companion © 2026
                    </p>
                </div>
            </body>
        </html>
        """
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = GMAIL_EMAIL
        msg['To'] = to_email
        
        # Attach HTML body
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        logger.info(f"Sending reset email to: {to_email}")
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_EMAIL, GMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Reset email sent successfully to: {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail authentication failed. Check GMAIL_EMAIL and GMAIL_PASSWORD in .env")
        return False
    except Exception as e:
        logger.error(f"Error sending reset email: {e}")
        return False

def send_otp_email(to_email, otp):
    """
    Send OTP via Gmail
    """
    try:
        if not GMAIL_EMAIL or not GMAIL_PASSWORD:
            logger.warning("Gmail not configured for OTP sending")
            return False

        subject = "🔐 Smart Companion - Your Password Reset OTP"
        
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #667eea;">Password Reset OTP</h2>
                    
                    <p>Hi,</p>
                    
                    <p>Your One-Time Password (OTP) to reset your password is:</p>
                    
                    <div style="background: #f0f0f0; padding: 20px; border-radius: 10px; text-align: center; font-family: monospace; font-size: 32px; letter-spacing: 5px; margin: 30px 0; font-weight: bold;">
                        {otp}
                    </div>
                    
                    <p style="color: #999; font-size: 12px;">
                        ⏰ This OTP expires in 5 minutes.<br>
                        If you didn't request this, please ignore this email.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="text-align: center; color: #999; font-size: 12px;">
                        Smart Companion © 2026
                    </p>
                </div>
            </body>
        </html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = GMAIL_EMAIL
        msg['To'] = to_email
        msg.attach(MIMEText(body, 'html'))
        
        logger.info(f"Sending OTP to: {to_email}")
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_EMAIL, GMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"OTP email sent successfully to: {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending OTP email: {e}")
        return False

# ============ PAGE ROUTES ============

@app.route('/')
def index():
    """Login page"""
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    """Signup page"""
    return render_template('signup.html')

@app.route('/password-reset')
def password_reset_page():
    """Password reset page"""
    return render_template('password-reset.html')

@app.route('/welcome')
def welcome():
    """Welcome/guest page"""
    return render_template('welcome.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

# ============ AUTH API - PASSWORD RESET (TOKEN METHOD) ============

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """
    Send password reset token via email
    """
    data = request.json
    email = data.get('email', '').strip()

    logger.info(f"Password reset request for: {email}")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    
    # Store token with expiration
    reset_tokens[email] = {
        'token': reset_token,
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)).isoformat()
    }

    logger.info(f"Reset token generated for: {email}")
    
    # Try to send email
    email_sent = send_reset_email(email, reset_token)

    return jsonify({
        "success": True,
        "message": "Password reset email sent" if email_sent else "Reset code generated (email not configured)",
        "token": reset_token if not email_sent else None  # Only return token if email failed
    }), 200


@app.route('/api/auth/confirm-reset', methods=['POST'])
def confirm_reset():
    """
    Confirm password reset with token
    Actual password update happens in Firebase (frontend)
    """
    data = request.json
    email = data.get('email', '').strip()
    token = data.get('token', '').strip()

    logger.info(f"Password reset confirmation for: {email}")

    if not email or not token:
        return jsonify({"error": "Missing email or token"}), 400

    # Check if token exists and is valid
    if email not in reset_tokens:
        return jsonify({"error": "No reset request found for this email"}), 404

    stored_token_data = reset_tokens[email]
    
    # Check if token matches
    if stored_token_data['token'] != token:
        return jsonify({"error": "Invalid reset token"}), 401

    # Check if token expired
    expires_at = datetime.fromisoformat(stored_token_data['expires_at'])
    if datetime.now() > expires_at:
        del reset_tokens[email]
        return jsonify({"error": "Reset token expired. Request a new one."}), 401

    # Token is valid
    logger.info(f"Token verified for: {email}")

    return jsonify({
        "success": True,
        "message": "Token verified. You can now reset your password."
    }), 200


@app.route('/api/auth/verify-token', methods=['POST'])
def verify_token():
    """
    Verify if a reset token is valid
    """
    data = request.json
    email = data.get('email', '').strip()
    token = data.get('token', '').strip()

    if not email or not token:
        return jsonify({"valid": False, "error": "Missing email or token"}), 400

    if email not in reset_tokens:
        return jsonify({"valid": False, "error": "No reset request found"}), 404

    stored_token_data = reset_tokens[email]
    
    if stored_token_data['token'] != token:
        return jsonify({"valid": False, "error": "Invalid token"}), 401

    expires_at = datetime.fromisoformat(stored_token_data['expires_at'])
    if datetime.now() > expires_at:
        del reset_tokens[email]
        return jsonify({"valid": False, "error": "Token expired"}), 401

    return jsonify({"valid": True, "email": email}), 200


@app.route('/api/auth/cleanup-reset-token', methods=['POST'])
def cleanup_reset_token():
    """
    Remove reset token after successful password change
    """
    data = request.json
    email = data.get('email', '').strip()

    if email in reset_tokens:
        del reset_tokens[email]
        logger.info(f"Reset token cleaned up for: {email}")

    return jsonify({"success": True}), 200

# ============ AUTH API - PASSWORD RESET (OTP METHOD) ============

@app.route('/api/auth/generate-otp', methods=['POST'])
@limiter.limit(RATE_LIMIT_OTP)
def generate_otp():
    """Generate and send OTP via email"""
    data = request.json
    email = data.get('email', '').strip()

    if not email:
        return jsonify({"error": "Email is required"}), 400

    logger.info(f"OTP generation request for: {email}")

    # Generate OTP
    otp = ''.join(random.choices(string.digits, k=OTP_LENGTH))
    
    # Store OTP with expiration
    otp_storage[email] = {
        'otp': otp,
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()
    }

    logger.info(f"OTP generated for: {email} (length: {len(otp)})")

    # Send OTP via email
    email_sent = send_otp_email(email, otp)

    if not email_sent:
        return jsonify({"error": "Failed to send OTP. Check email configuration."}), 500

    return jsonify({
        "success": True,
        "message": "OTP sent to email"
    }), 200


@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP"""
    data = request.json
    email = data.get('email', '').strip()
    otp = data.get('otp', '').strip()

    logger.info(f"OTP verification for: {email}")

    if not email or not otp:
        return jsonify({"error": "Missing email or OTP"}), 400

    if email not in otp_storage:
        return jsonify({"error": "No OTP found for this email"}), 404

    otp_data = otp_storage[email]
    
    if otp_data['otp'] != otp:
        return jsonify({"error": "Invalid OTP"}), 401

    expires_at = datetime.fromisoformat(otp_data['expires_at'])
    if datetime.now() > expires_at:
        del otp_storage[email]
        return jsonify({"error": "OTP expired"}), 401

    logger.info(f"OTP verified for: {email}")
    return jsonify({"valid": True, "email": email}), 200


# Store verified reset sessions (email -> timestamp)
verified_reset_sessions = {}

@app.route('/api/auth/verify-otp-for-reset', methods=['POST'])
def verify_otp_for_reset():
    """Verify OTP and create a verified reset session"""
    data = request.json
    email = data.get('email', '').strip()
    otp = data.get('otp', '').strip()

    logger.info(f"OTP verification for password reset: {email}")

    if not email or not otp:
        return jsonify({"error": "Missing email or OTP"}), 400

    if email not in otp_storage:
        return jsonify({"error": "No OTP found"}), 404

    otp_data = otp_storage[email]
    
    if otp_data['otp'] != otp:
        return jsonify({"error": "Invalid OTP"}), 401

    expires_at = datetime.fromisoformat(otp_data['expires_at'])
    if datetime.now() > expires_at:
        del otp_storage[email]
        return jsonify({"error": "OTP expired"}), 401

    # OTP is valid, clean it up and create verified session
    del otp_storage[email]
    
    # Create a 10-minute verified session
    verified_reset_sessions[email] = {
        'verified_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(minutes=10)).isoformat()
    }

    logger.info(f"OTP verified, reset session created for: {email}")
    
    return jsonify({
        "success": True,
        "message": "OTP verified. You can now set your new password."
    }), 200


@app.route('/api/auth/reset-password-with-otp', methods=['POST'])
def reset_password_with_otp():
    """Reset password using verified session + current password"""
    import requests
    
    data = request.json
    email = data.get('email', '').strip()
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')

    logger.info(f"Password reset request for: {email}")

    if not email or not current_password or not new_password:
        return jsonify({"error": "Missing required fields"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    # Check if there's a verified reset session
    if email not in verified_reset_sessions:
        return jsonify({"error": "No verified reset session. Please verify OTP first."}), 403

    session_data = verified_reset_sessions[email]
    expires_at = datetime.fromisoformat(session_data['expires_at'])
    
    if datetime.now() > expires_at:
        del verified_reset_sessions[email]
        return jsonify({"error": "Reset session expired. Please start over."}), 403

    logger.info(f"Verified reset session found for: {email}")
    
    try:
        firebase_api_key = FIREBASE_API_KEY
        
        # Step 1: Sign in with current password to get idToken
        signin_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={firebase_api_key}"
        
        logger.info("Signing in with current password...")
        
        signin_response = requests.post(signin_url, json={
            "email": email,
            "password": current_password,
            "returnSecureToken": True
        })
        
        signin_data = signin_response.json()
        
        if 'error' in signin_data:
            error_msg = signin_data['error'].get('message', 'Unknown error')
            logger.error(f"Sign-in error: {error_msg}")
            if 'INVALID_PASSWORD' in error_msg or 'INVALID_LOGIN_CREDENTIALS' in error_msg:
                return jsonify({"error": "Incorrect current password"}), 401
            return jsonify({"error": f"Sign-in failed: {error_msg}"}), 500
        
        id_token = signin_data.get('idToken')
        
        if not id_token:
            logger.error("No idToken in response")
            return jsonify({"error": "Authentication failed"}), 500
        
        # Step 2: Update password using the idToken
        update_url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={firebase_api_key}"
        
        logger.info("Updating password...")
        
        update_response = requests.post(update_url, json={
            "idToken": id_token,
            "password": new_password,
            "returnSecureToken": True
        })
        
        update_data = update_response.json()
        
        if 'error' in update_data:
            error_msg = update_data['error'].get('message', 'Unknown error')
            logger.error(f"Password update error: {error_msg}")
            return jsonify({"error": f"Failed to update password: {error_msg}"}), 500
        
        # Clean up verified session
        del verified_reset_sessions[email]
        
        logger.info(f"Password updated successfully for: {email}")
        
        return jsonify({
            "success": True,
            "message": "Password reset successful!"
        }), 200
        
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        return jsonify({"error": "Failed to reset password"}), 500


@app.route('/api/auth/cleanup-otp', methods=['POST'])
def cleanup_otp():
    """Remove OTP after successful password change"""
    data = request.json
    email = data.get('email', '').strip()

    if email in otp_storage:
        del otp_storage[email]
        logger.info(f"OTP cleaned up for: {email}")

    return jsonify({"success": True}), 200

# ============ API ROUTES - TASK DECOMPOSITION ============

@app.route('/api/decompose', methods=['POST'])
@limiter.limit(RATE_LIMIT_DECOMPOSE)
def decompose_task():
    """
    Break down a task into micro-wins using Gemini AI
    """
    data = request.json
    goal = data.get('goal', '').strip() if data else ''
    
    # Input validation
    if not goal:
        return jsonify({"error": "No goal provided"}), 400
    
    if len(goal) > MAX_GOAL_LENGTH:
        return jsonify({"error": f"Goal must be under {MAX_GOAL_LENGTH} characters"}), 400

    try:
        logger.info(f"Decomposing goal: {goal[:100]}...")
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=goal,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json"
            )
        )
        
        logger.info("Got response from Gemini")
        
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        steps = json.loads(clean_text)
        
        logger.info(f"Parsed {len(steps)} steps successfully")
        
        return jsonify({
            "success": True,
            "steps": steps
        }), 200
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON Parse Error: {str(e)}")
        return jsonify({"error": "Failed to parse AI response"}), 500
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Decompose error: {error_msg}")
        
        if "429" in error_msg or "quota" in error_msg.lower():
            return jsonify({"error": "Rate limit reached. Try again later."}), 429
        
        if "invalid_api_key" in error_msg or "unauthorized" in error_msg.lower():
            return jsonify({"error": "Invalid API key"}), 401
        
        return jsonify({"error": "Failed to decompose task"}), 500

# ============ TASK TRACKING API ============

# In-memory task storage (should be moved to database)
task_completions = {}

@app.route('/api/task/<task_id>/complete-step', methods=['POST'])
def complete_task_step(task_id: str):
    """
    Mark a task step as completed
    """
    try:
        auth_token = request.headers.get('Authorization', '')
        
        if not auth_token:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.json or {}
        step_index = data.get('step_index', 0)
        
        # Store completion record
        if task_id not in task_completions:
            task_completions[task_id] = []
        
        task_completions[task_id].append({
            'step_index': step_index,
            'completed_at': datetime.now().isoformat()
        })
        
        logger.info(f"Task step completed: {task_id} (step {step_index})")
        
        return jsonify({
            "success": True,
            "message": "Task step recorded",
            "task_id": task_id,
            "step_index": step_index
        }), 200
        
    except Exception as e:
        logger.error(f"Error completing task step: {str(e)}")
        return jsonify({"error": "Failed to record task completion"}), 500

# ============ USER PROFILE API ============

@app.route('/api/user/profile', methods=['GET'])
def get_profile():
    """Get user profile"""
    return jsonify({
        "id": 0,
        "email": "user@example.com",
        "username": "User",
        "created_at": datetime.now().isoformat(),
        "theme_preference": "ocean",
        "total_tasks_completed": 0
    }), 200

@app.route('/api/user/theme', methods=['POST'])
def set_theme():
    """Set user theme preference"""
    data = request.json
    theme = data.get('theme')
    
    if not theme:
        return jsonify({"error": "Theme not specified"}), 400
    
    return jsonify({
        "success": True,
        "theme": theme
    }), 200

# ============ HEALTH CHECK ============

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }), 200

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 error: {request.path}")
    return jsonify({"success": False, "error": "Route not found"}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {error}")
    return jsonify({"success": False, "error": "Internal server error"}), 500

# ============ MAIN ============

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("🚀 GLADE AI - EXECUTIVE FUNCTION COACH")
    logger.info("="*60)
    
    # Log configuration status
    logger.info(f"Flask initialized")
    logger.info(f"Gemini API: {'✅ Configured' if os.getenv('GEMINI_API_KEY') else '❌ Not configured'}")
    logger.info(f"Secret key: ✅ Configured")
    logger.info(f"Firebase: {'✅ Configured' if os.getenv('FIREBASE_API_KEY') else '❌ Not configured'}")
    logger.info(f"Gmail: {'✅ ' + os.getenv('GMAIL_EMAIL', '') if os.getenv('GMAIL_EMAIL') else '⚠️ Not configured'}")
    logger.info(f"Rate limiting: ✅ Enabled")
    logger.info(f"CORS: ✅ Enabled")
    logger.info(f"Security headers: ✅ Enabled")
    logger.info(f"🌐 Server: {os.getenv('APP_URL', 'http://localhost:5000')}")
    logger.info("="*60)
    
    app.run(debug=True, host='127.0.0.1', port=5000)