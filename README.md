# 📱 THE FEED

A full-stack cross-platform social networking application designed for sharing quick thoughts, engaging in threaded discussions, and customizing digital identities. Built with a modern, high-performance tech stack.

## 🛠️ Tech Stack

**Client (Frontend):**
* Framework: Flutter / Dart
* Targets: Android (.apk) & Windows Desktop
* Architecture: Stateful Widget State Management, REST API Integration

**Server (Backend):**
* Framework: FastAPI (Python)
* Database: PostgreSQL (via Neon.tech)
* ORM: SQLAlchemy (Asynchronous)
* Authentication: JWT (JSON Web Tokens) & bcrypt password hashing
* Deployment: Koyeb (Serverless backend hosting)

---

## ✨ Key Features

* **Secure Authentication:** Complete registration and login system with encrypted passwords and stateless JWT session management.
* **Global Feed:** Scrollable timeline of global transmissions featuring timestamps, author details, and emoji tags.
* **Deeply Nested Threads:** Recursive, multi-level threaded comment section (similar to Reddit) allowing infinite-depth replies with visual indentation.
* **Interactive Reactions:** Real-time Like and Dislike toggle system linked directly to the database.
* **Entity Profiles:** 
  * View your personal transmission history and total interaction stats.
  * Tappable avatars in the feed to view read-only profiles of other users.
  * Update Display Name, Username, and select custom Emoji Avatars globally.
* **Account Control:** Secure password reset flows and a complete account deletion mechanism that scrubs all associated data from the database.

---

## 🏗️ Local Development Setup

### 1. Backend Setup (FastAPI)
```bash
# Clone the repository
git clone [https://github.com/YourUsername/the_feed.git](https://github.com/YourUsername/the_feed.git)
cd the_feed/backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (Create a .env file)
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
JWT_SECRET=your_super_secret_key

# Run the server
uvicorn main:app --reload
