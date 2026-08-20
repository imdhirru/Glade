# GLADE AI - BREAKDOWN YOUR PROBLEMS

A Flask-based web application designed to act as an executive function coach for individuals with ADHD/Autism. It leverages Google's Generative AI (Gemini) to break down overwhelming tasks into manageable "Micro-Wins".

## Features 🚀

- **Micro-Win Task Decomposition**: Uses Gemini AI to break complex tasks into simple, actionable steps (under 10 minutes each).
- **Authentication**: Secure user authentication flow (Login/Signup).
- **Password Reset**: robust password reset flow supporting both secure tokens and OTP verification via email.
- **User Profile**: Basic user profile management.
- **Dark/Light Mode**: User theme preferences.
- **Health Check**: Simple API health monitoring.

## Tech Stack 🛠️

- **Backend**: Python, Flask
- **Database**: Firebase (Authentication/Firestore)
- **AI**: Google Gemini (Generative AI)
- **Email**: SMTP (Gmail) for OTPs and reset links
- **Frontend**: HTML, CSS (Templates), Javascript

## Getting Started 🏁

### Prerequisites

- Python 3.8+
- A Google Cloud Project with Gemini API enabled
- Firebase Project credentials
- Gmail account (for sending emails)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/imdhirru/Glade.git
   cd Glade
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the root directory and add your credentials:
   ```env
   SECRET_KEY=your_secret_key
   GEMINI_API_KEY=your_gemini_api_key
   FIREBASE_API_KEY=your_firebase_api_key
   GMAIL_EMAIL=your_email@gmail.com
   GMAIL_PASSWORD=your_app_password
   ```

### Running the Application

```bash
python app.py
```
The application will be available at `http://localhost:5000`.

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request.
