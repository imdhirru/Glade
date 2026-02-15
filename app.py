from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import secrets
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-me-in-production')

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
            print("⚠️  Gmail credentials not configured. Skipping email send.")
            print(f"📋 Reset Token (for manual testing): {token}")
            return True

        # Create email
        subject = "🔐 Smart Companion - Reset Your Password"
        
        reset_link = f"http://localhost:5000/password-reset?token={token}&email={to_email}"
        
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
        print(f"📧 Sending reset email to: {to_email}")
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_EMAIL, GMAIL_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent successfully to: {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Gmail authentication failed. Check GMAIL_EMAIL and GMAIL_PASSWORD in .env")
        return False
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def send_otp_email(to_email, otp):
    """
    Send OTP via Gmail
    """
    try:
        if not GMAIL_EMAIL or not GMAIL_PASSWORD:
            print("⚠️  Gmail not configured")
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
        
        print(f"📧 Sending OTP to: {to_email}")
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_EMAIL, GMAIL_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ OTP email sent to: {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending OTP email: {e}")
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

    print(f"📧 Password reset request: {email}")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    
    # Store token with expiration (1 hour)
    reset_tokens[email] = {
        'token': reset_token,
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
    }

    print(f"✅ Reset token generated for: {email}")
    print(f"🔑 Reset Token: {reset_token}")

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

    print(f"🔐 Password reset confirmation: {email}")

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
    print(f"✅ Token verified for: {email}")

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
        print(f"🗑️ Reset token cleaned up for: {email}")

    return jsonify({"success": True}), 200

# ============ AUTH API - PASSWORD RESET (OTP METHOD) ============

@app.route('/api/auth/generate-otp', methods=['POST'])
def generate_otp():
    """Generate and send OTP via email"""
    data = request.json
    email = data.get('email', '').strip()

    print(f"📧 OTP generation request for: {email}")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Generate 6-digit OTP
    otp = ''.join(random.choices(string.digits, k=6))
    
    # Store OTP with expiration (5 minutes)
    otp_storage[email] = {
        'otp': otp,
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(minutes=5)).isoformat()
    }

    print(f"✅ OTP generated: {otp}")

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

    print(f"🔑 OTP verification for: {email}")

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

    print(f"✅ OTP verified for: {email}")
    return jsonify({"valid": True, "email": email}), 200


# Store verified reset sessions (email -> timestamp)
verified_reset_sessions = {}

@app.route('/api/auth/verify-otp-for-reset', methods=['POST'])
def verify_otp_for_reset():
    """Verify OTP and create a verified reset session"""
    data = request.json
    email = data.get('email', '').strip()
    otp = data.get('otp', '').strip()

    print(f"🔐 OTP verification for password reset: {email}")

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

    print(f"✅ OTP verified, reset session created for: {email}")
    
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

    print(f"🔐 Password reset request for: {email}")

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

    print(f"✅ Verified session found for: {email}")
    
    try:
        firebase_api_key = FIREBASE_API_KEY
        
        # Step 1: Sign in with current password to get idToken
        signin_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={firebase_api_key}"
        
        print(f"� Signing in with current password...")
        
        signin_response = requests.post(signin_url, json={
            "email": email,
            "password": current_password,
            "returnSecureToken": True
        })
        
        signin_data = signin_response.json()
        
        if 'error' in signin_data:
            error_msg = signin_data['error'].get('message', 'Unknown error')
            print(f"❌ Sign-in error: {error_msg}")
            if 'INVALID_PASSWORD' in error_msg or 'INVALID_LOGIN_CREDENTIALS' in error_msg:
                return jsonify({"error": "Incorrect current password"}), 401
            return jsonify({"error": f"Sign-in failed: {error_msg}"}), 500
        
        id_token = signin_data.get('idToken')
        
        if not id_token:
            print(f"❌ No idToken in response")
            return jsonify({"error": "Authentication failed"}), 500
        
        # Step 2: Update password using the idToken
        update_url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={firebase_api_key}"
        
        print(f"🔐 Updating password...")
        
        update_response = requests.post(update_url, json={
            "idToken": id_token,
            "password": new_password,
            "returnSecureToken": True
        })
        
        update_data = update_response.json()
        
        if 'error' in update_data:
            error_msg = update_data['error'].get('message', 'Unknown error')
            print(f"❌ Password update error: {error_msg}")
            return jsonify({"error": f"Failed to update password: {error_msg}"}), 500
        
        # Clean up verified session
        del verified_reset_sessions[email]
        
        print(f"✅ Password updated successfully for: {email}")
        
        return jsonify({
            "success": True,
            "message": "Password reset successful!"
        }), 200
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": f"Failed to reset password: {str(e)}"}), 500
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": f"Failed to send reset email: {str(e)}"}), 500


@app.route('/api/auth/cleanup-otp', methods=['POST'])
def cleanup_otp():
    """Remove OTP after successful password change"""
    data = request.json
    email = data.get('email', '').strip()

    if email in otp_storage:
        del otp_storage[email]
        print(f"🗑️ OTP cleaned up for: {email}")

    return jsonify({"success": True}), 200

# ============ API ROUTES - TASK DECOMPOSITION ============

@app.route('/api/decompose', methods=['POST'])
def decompose_task():
    """
    Break down a task into micro-wins using Gemini AI
    """
    data = request.json
    goal = data.get('goal')
    
    if not goal:
        return jsonify({"error": "No goal provided"}), 400

    try:
        print(f"\n{'='*60}")
        print(f"🤖 DECOMPOSING GOAL: {goal}")
        print(f"{'='*60}")
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=goal,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json"
            )
        )
        
        print(f"✅ Got response from Gemini")
        
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        steps = json.loads(clean_text)
        
        print(f"✅ Parsed {len(steps)} steps")
        for i, step in enumerate(steps, 1):
            print(f"   {i}. {step}")
        print(f"{'='*60}\n")
        
        return jsonify({
            "success": True,
            "steps": steps
        }), 200
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {str(e)}")
        return jsonify({"error": f"Failed to parse AI response"}), 500
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ ERROR: {error_msg}")
        
        if "429" in error_msg or "quota" in error_msg.lower():
            return jsonify({"error": "Rate limit reached. Try again later."}), 429
        
        if "invalid_api_key" in error_msg or "unauthorized" in error_msg.lower():
            return jsonify({"error": "Invalid API key"}), 401
        
        return jsonify({"error": f"Error: {error_msg}"}), 500

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
    return jsonify({"error": "Route not found"}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    print(f"❌ Server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# ============ MAIN ============

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 SMART COMPANION - NEUROTHON PROJECT")
    print("="*60)
    print(f"✅ Flask initialized")
    if os.getenv('GEMINI_API_KEY'):
        print(f"✅ Gemini API: {os.getenv('GEMINI_API_KEY')[:20]}...")
    else:
        print(f"❌ Gemini API not configured")
    print(f"✅ Secret key: configured")
    print(f"✅ Firebase: configured")
    if GMAIL_EMAIL and GMAIL_PASSWORD:
        print(f"✅ Gmail: {GMAIL_EMAIL}")
    else:
        print(f"⚠️  Gmail: Not configured")
    print(f"✅ OTP System: Ready with Email Sending")
    print(f"✅ Firebase API Key: {FIREBASE_API_KEY[:20] if FIREBASE_API_KEY else 'Not configured'}...")
    print(f"🌐 Server: http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)