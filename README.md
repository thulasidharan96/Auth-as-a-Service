# 🔐 Authentication as a Service (AaaS)

Welcome to the **Authentication as a Service (AaaS)** platform! 

This repository contains a production-ready, highly secure, and extremely fast system designed to handle everything related to **User Identity and Access Management**. Think of this system as the "bouncer" and the "vault" for any software application. It securely registers users, verifies who they say they are using modern methods (like face ID, magic links, or passwords), and issues digital "passes" so they can securely access other features of the app.

---

## 📖 High-Level Concept: What does this do?

If you are building an application, you don't want to build login systems from scratch every time. Doing so is risky, expensive, and complex. This platform acts as a standalone **microservice**. You install this, and it handles all your security.

Here are the concepts built into this system, explained simply:

1. **Passkeys (FIDO2 / WebAuthn):**
   * *What it is:* Allowing users to log in using their fingerprint, FaceID, or a YubiKey hardware device.
   * *Why it matters:* It completely eliminates passwords, making it physically impossible for hackers to "guess" or "phish" a password over the internet.
   
2. **SSO / OAuth2 (Google & GitHub login):**
   * *What it is:* "Log in with Google" or "Log in with GitHub".
   * *Why it matters:* Users can log in with one click without creating a new password. The system handles talking back and forth with Google securely.

3. **Magic Links:**
   * *What it is:* A user enters their email, and the system sends them a secure, temporary link. Clicking the link logs them in directly.
   * *Why it matters:* It provides a highly secure "passwordless" experience for users who don't want to use biometrics.

4. **Time-based OTP (Google Authenticator):**
   * *What it is:* Two-Factor Authentication (2FA) where a user must enter a 6-digit code from an app on their phone.
   * *Why it matters:* Even if a hacker steals a password, they cannot log in without holding the user's physical phone.

5. **Sessions & API Keys:**
   * *What it is:* Allowing developers or internal tools to generate strict, long-lasting "robot" keys to communicate with your systems. And allowing users to see every device currently logged into their account, so they can remotely kick out a suspicious login.

---

## 🏗️ Detailed Architecture & Directory Structure

The codebase is organized using a pattern called **Clean Architecture**. This means different logic is separated into independent folders, preventing the code from becoming messy as it scales.

Here is an overview of what each folder does, in simple terms:

```text
app/
├── api/
│   │   # Think of this as the "Front Door". It receives HTTP requests (like a website form submission) 
│   │   # and routes them to the correct backend service.
│   └── v1/
│       ├── apikeys/   # Endpoints for generating and revoking developer API keys.
│       ├── auth/      # Endpoints for Logging in, Registering, Magic Links, and Passkeys.
│       └── sessions/  # Endpoints for viewing active logged-in devices and logging them out.
│
├── core/
│   │   # The "Engine Room". This holds the fundamental settings required for the app to turn on.
│   ├── config.py      # Reads the `.env` file to pull secret keys and passwords.
│   ├── database.py    # Establishes the connection to the PostgreSQL database.
│   └── logging.py     # Ensures everything the server does gets written out natively as JSON for monitoring.
│
├── dependencies/
│   │   # "The Bouncers". Before a user can reach a protected feature, 
│   │   # these files check their digital tokens to ensure they are logged in.
│   └── auth.py        
│
├── middleware/
│   │   # "The Security Cameras". Code that watches every single request passing in and out.
│   └── tracing.py     # Measures how fast requests take and tags them with an ID for easy tracking.
│
├── models/            
│   │   # The "Blueprint". Describes exactly how data is structured on the hard drive (in the database).
│   # (e.g., users.py, credentials.py, api_key.py)
│
├── repositories/      
│   │   # The "Librarians". These files are the ONLY ones allowed to read, write, or delete 
│   │   # from the database. This keeps database logic isolated safely.
│
├── schemas/           
│   │   # The "Customs Inspectors". When a user sends data to us (like a password), 
│   │   # these files double-check that the data is formatted correctly before processing it.
│
├── services/          
│   │   # The "Brains" or "Business Logic". This is where the heavy lifting happens.
│   ├── auth.py        # Validates passwords against hashes, issues tracking tokens, configures 2FA.
│   ├── oauth_service.py # Verifies Google/Github identity payloads.
│   └── webauthn_service.py # Mathematically validates biometric fingerprints to math algorithms.
│
├── static/            
│   │   # The "Frontend". The visual HTML, CSS, and JS files that make up the Command Center Interface.
│   # (index.html, style.css, app.js)
│
└── utils/             
    │   # "The Toolbelt". Small, standalone helper programs that do one specific job really well.
    ├── magic_link.py  # Generates short-term cryptographic links.
    ├── oauth.py       # Configures the integration to external providers.
    ├── otp.py         # The mathematical generator behind Google Authenticator codes.
    ├── security.py    # The raw cryptography file (Password hashing & token generation).
    └── webauthn.py    # Interacts with the web browser to request local Fingerprints.
```

---

## 📖 Real-World User Flows

How does the data actually move through this system? Let's trace back standard real-world usage scenarios.

### Scenario 1: A User Forgets Their Password (Magic Link Flow)
1. **The Request:** The user navigates to the login screen and types their email address into the "Magic Link" box.
2. **The API Doorway:** The frontend sends a request to the backend at `/api/v1/auth/magic-link`.
3. **The Brains:** The `AuthService` logic looks up the email. It instructs `utils/magic_link.py` to create a tiny digital puzzle (a JSON Web Token) that only lasts for 15 minutes.
4. **The Database:** The system logs an audit trail using the `AuditLog` model ("User requested magic link from IP 192.168.x.x").
5. **The Redemption:** The user clicks the link. The `AuthService` extracts the token, confirms it isn't expired, and instantly logs them in, bypassing passwords securely!

### Scenario 2: Connecting an Integration (API Keys)
1. **The Goal:** An enterprise team wants to connect an automated billing machine to your backend silently.
2. **The Action:** An administrator uses the Command Center to name an API key "Billing System".
3. **The Creation:** The backend `APIKeyCreate` endpoint calls Python's native `secrets` module to generate a heavy mathematical string. 
4. **The Hashing:** It mathematically scrambles (hashes) this string and stores *only the scrambled version* in the database via the `APIKey` model.
5. **The Reveal:** It returns the original text to the screen *exactly once*. If the administrator loses it, they cannot retrieve it—they must generate a completely new key. This protects the company from database leaks.

---

## 🛠️ The Tech Stack (What powers this?)

While the concepts are beginner-friendly, the tech stack is ultra-modern and designed for immense enterprise scale:

*   **FastAPI:** The fastest possible server framework for Python, capable of handling tens of thousands of concurrent connections smoothly.
*   **PostgreSQL & AsyncPG:** A highly reliable enterprise database system processing information asynchronously, meaning it won't freeze when multiple queries hit simultaneously.
*   **Alembic:** A version-control system for the database (allowing us to automatically add or modify tables as the platform evolves).
*   **Argon2-cffi:** The global gold-standard hashing algorithm. It ensures that even if hackers stole the entire database, it would take supercomputers decades to guess a single password.

---

## 🏁 How to Start testing Locally

### 1. Pre-requisites
Ensure you have **Docker**, **Docker Compose**, and **uv** (a blazing fast Python package manager) installed on your computer.

### 2. Configuration
Copy the template environment file to activate your app's variables:
```bash
cp .env.example .env
```

### 3. Start Database
Turn on your PostgreSQL database silently in the background using Docker:
```bash
docker-compose up -d db redis
```

### 4. Create the Database Tables
Sync the code models directly structured into physical live database tables:
```bash
uv run alembic upgrade head
```

### 5. Launch the Server
Start the core Python application engine:
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Explore Visuals
Open a browser and navigate to **`http://localhost:8000/`**. You will be greeted by a complete, fully functional graphical interface (The Command Center) where you can visually test creating users, generating keys, and simulating Passkeys!

For deep developer-level documentation for integrations, visit the interactive OpenAPI Portal at **`http://localhost:8000/docs`**.
