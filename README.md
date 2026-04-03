<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-3.1.2-000000?style=for-the-badge&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/SocketIO-010101?style=for-the-badge&logo=socket.io&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
</p>

<h1 align="center">🔄 SkillSwap Pro</h1>

<p align="center">
  <strong>A modern, gamified skill-sharing platform where users exchange knowledge and grow together.</strong>
</p>

<p align="center">
  <a href="#features-">Features</a> •
  <a href="#tech-stack-">Tech Stack</a> •
  <a href="#setup--installation-">Setup</a> •
  <a href="#project-structure-">Structure</a> •
  <a href="#api-routes-">API</a> •
  <a href="#contributing-">Contributing</a>
</p>

---

## Features ✨

### 🔐 Authentication & Security
- Secure registration & login with Werkzeug password hashing
- **Password reset via email** — styled HTML emails sent through Gmail SMTP
- CSRF protection on all forms (Flask-WTF)
- Rate limiting on sensitive endpoints (Flask-Limiter)
- Secure session cookies with HTTPOnly & SameSite flags
- Input validation with WTForms & email-validator
- SQL injection prevention via SQLAlchemy ORM

### 🎯 Smart Skill Matching
- **Fuzzy matching algorithm** — finds users even with partial skill name matches
- **Weighted scoring system:**
  - 🧩 Mutual skill compatibility (25 pts per match)
  - ⭐ User reputation & rating (10 pts per rating point)
  - 📈 Experience level / XP (scaled)
  - 🌍 Timezone bonus (+10 pts for same timezone)
- Filter matches by skill category
- Skill proficiency levels: Beginner → Intermediate → Expert

### 💬 Real-Time Chat
- WebSocket-powered messaging via Flask-SocketIO
- Per-swap chat rooms with message history
- Unread message counter in navigation
- Read/unread message tracking

### 🏆 Gamification System
- **XP Points:**
  - +10 XP — Adding a skill
  - +50 XP — Completing a swap
  - +50 XP — Receiving a review
- **Level Progression:** Beginner 🌱 → Skilled 🚀 → Expert 🔥 → Master 👑
- **Achievement Badges:**
  | Badge | Requirement |
  |-------|------------|
  | 🤝 First Swap | Complete 1 swap |
  | ⭐ Rising Star | Earn 200 XP |
  | 🏅 Skill Master | Earn 500 XP |
  | 🧑‍🏫 Trusted Mentor | Receive 5+ reviews |

### 📋 Core Platform
- **Skill Marketplace** — Browse users offering/wanting skills across 8 categories
- **Swap Requests** — Send, accept, reject, and complete skill exchanges
- **Review System** — Rate (1-5 stars) and comment after completed swaps
- **User Profiles** — Customizable bio, profile picture upload (2MB limit), timezone
- **Notifications** — Real-time alerts for swap requests and messages
- **Dashboard** — Paginated view of matched users with compatibility scores

---

## Tech Stack 🛠️

| Layer | Technology |
|-------|-----------|
| **Backend** | Flask 3.1.2, Flask-Login, Flask-SQLAlchemy, Flask-Migrate |
| **Real-Time** | Flask-SocketIO, python-socketio, python-engineio |
| **Database** | SQLite (dev) / PostgreSQL (production-ready) |
| **Email** | Flask-Mail with Gmail SMTP |
| **Frontend** | HTML5, CSS3, JavaScript, Jinja2 Templates |
| **Auth** | Flask-Login + Werkzeug password hashing |
| **Forms** | Flask-WTF, WTForms, email-validator |
| **Security** | CSRF Protection, Rate Limiting, Secure Sessions |
| **Migrations** | Flask-Migrate (Alembic) |
| **Environment** | python-dotenv |

---

## Database Models 🗄️

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│     User     │────▶│    Skill     │     │    Badge     │
│──────────────│     │──────────────│     │──────────────│
│ id           │     │ id           │     │ id           │
│ username     │     │ name         │     │ name         │
│ email        │     │ category     │     │ description  │
│ password     │     │ type         │     │ icon         │
│ bio          │     │ proficiency  │     └──────┬───────┘
│ xp / badge   │     │ user_id (FK) │            │
│ profile_pic  │     └──────────────┘     ┌──────┴───────┐
│ rating       │                          │  UserBadge   │
│ timezone     │◀─────────────────────────│──────────────│
│ created_at   │     ┌──────────────┐     │ user_id (FK) │
└──────┬───────┘     │ SwapRequest  │     │ badge_id(FK) │
       │             │──────────────│     │ earned_at    │
       │             │ sender_id    │     └──────────────┘
       ├────────────▶│ receiver_id  │
       │             │ status       │     ┌──────────────┐
       │             │ accepted_at  │     │ ChatMessage  │
       │             │ completed_at │────▶│──────────────│
       │             └──────────────┘     │ swap_id (FK) │
       │                                  │ sender_id    │
       │             ┌──────────────┐     │ message      │
       ├────────────▶│   Review     │     │ is_read      │
       │             │──────────────│     └──────────────┘
       │             │ reviewer_id  │
       │             │ reviewed_id  │     ┌──────────────┐
       │             │ rating       │     │ Notification │
       │             │ comment      │     │──────────────│
       │             └──────────────┘     │ user_id (FK) │
       └─────────────────────────────────▶│ message      │
                                          │ is_read      │
                                          └──────────────┘
```

---

## Setup & Installation 🚀

### Prerequisites
- Python 3.9+
- pip (Python package manager)
- Gmail account with [App Password](https://myaccount.google.com/apppasswords) (for password reset emails)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/luckyyyroyyy/Skill-Swap.git
   cd Skills-Swap
   ```

2. **Create & activate virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your settings:
   ```env
   SECRET_KEY=your-secret-key-here
   FLASK_ENV=development
   DATABASE_URL=sqlite:///skillswap.db
   UPLOAD_FOLDER=static/profile_pics

   # Gmail SMTP (for password reset emails)
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-16-char-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   ```

5. **Initialize the database**
   ```bash
   python -m flask db upgrade
   ```
   Or manually:
   ```python
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

6. **Run the application**
   ```bash
   python app.py
   ```
   The app will be available at **http://localhost:5000** 🎉

---

## Project Structure 📁

```
Skills-Swap/
├── app.py                  # Flask app, SocketIO events, context processors
├── config.py               # Config classes (Dev / Prod / Test)
├── extensions.py           # Flask extensions (DB, Login, Limiter, Mail, SocketIO)
├── models.py               # SQLAlchemy models (User, Skill, Swap, Review, etc.)
├── forms.py                # WTForms (Registration, Login, Skills, Reviews, Reset)
├── utils.py                # XP, rating, matching, badge & notification systems
├── seed.py                 # Database seeding script
├── test_app.py             # Unit tests
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
│
├── routes/                 # Blueprint modules
│   ├── __init__.py         # Blueprint exports
│   ├── main.py             # Landing page
│   ├── auth.py             # Register, login, logout, password reset
│   ├── user.py             # Profile, dashboard, skills management
│   ├── swap.py             # Swap requests, reviews, matching
│   └── chat.py             # Real-time messaging
│
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Base layout with nav & scripts
│   ├── landing.html        # Public landing page
│   ├── register.html       # Registration form
│   ├── login.html          # Login form
│   ├── reset_password_request.html  # Forgot password
│   ├── reset_password.html # Password reset form
│   ├── dashboard.html      # Main dashboard with matches
│   ├── profile.html        # User profile view
│   ├── edit_profile.html   # Profile editor with avatar upload
│   ├── my_swaps.html       # Swap request management
│   ├── matches.html        # Skill matching results
│   ├── chat.html           # Real-time chat interface
│   └── notifications.html  # Notification center
│
├── static/                 # Static assets
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript files
│   ├── img/                # Images & icons
│   └── profile_pics/       # User uploaded avatars
│
├── migrations/             # Flask-Migrate / Alembic
│   ├── versions/           # Migration scripts
│   ├── env.py              # Migration environment
│   └── alembic.ini         # Alembic configuration
│
└── instance/               # Instance-specific files
    └── skillswap.db        # SQLite database
```

---

## API Routes 📡

### 🔓 Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET/POST` | `/register` | User registration |
| `GET/POST` | `/login` | User login |
| `GET` | `/logout` | Logout (auth required) |
| `GET/POST` | `/reset_password_request` | Request password reset email |
| `GET/POST` | `/reset_password/<token>` | Reset password with token |

### 👤 User & Profile
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard` | Dashboard with matched users |
| `GET/POST` | `/profile/<username>` | View user profile |
| `GET/POST` | `/edit_profile` | Edit profile (bio, avatar, timezone) |
| `POST` | `/add_skill` | Add a new skill |

### 🔄 Swaps & Reviews
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/send_swap/<user_id>` | Send swap request |
| `GET/POST` | `/my-swaps` | View all swap requests |
| `GET` | `/accept/<swap_id>` | Accept a swap |
| `GET` | `/reject/<swap_id>` | Reject a swap |
| `GET` | `/complete/<swap_id>` | Mark swap as completed |
| `POST` | `/submit_review/<user_id>` | Submit review for user |

### 💬 Chat & Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET/POST` | `/chat/<swap_id>` | Chat for a specific swap |
| `GET` | `/notifications` | View all notifications |

### 🔌 WebSocket Events
| Event | Direction | Description |
|-------|-----------|-------------|
| `join_room` | Client → Server | Join a chat room |
| `send_message` | Client → Server | Send a chat message |
| `receive_message` | Server → Client | Receive a chat message |
| `new_notification` | Server → Client | Real-time notification push |

---

## Environment Variables 🔐

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `dev-secret-key...` | Flask secret key **(change in production!)** |
| `FLASK_ENV` | `development` | `development` / `production` / `testing` |
| `DATABASE_URL` | `sqlite:///skillswap.db` | Database connection string |
| `UPLOAD_FOLDER` | `static/profile_pics` | Profile picture upload path |
| `DEBUG` | `True` | Enable debug mode |
| `MAIL_SERVER` | `smtp.gmail.com` | SMTP server address |
| `MAIL_PORT` | `587` | SMTP port (587 for TLS) |
| `MAIL_USE_TLS` | `True` | Enable TLS encryption |
| `MAIL_USERNAME` | — | Gmail address |
| `MAIL_PASSWORD` | — | Gmail App Password (16-char) |
| `MAIL_DEFAULT_SENDER` | — | Default "From" email address |

---

## Testing 🧪

```bash
pip install pytest
pytest test_app.py -v
```

Tests cover:
- ✅ User model operations
- ✅ Skill management (CRUD)
- ✅ Swap request lifecycle
- ✅ Matching algorithm accuracy
- ✅ Badge award system
- ✅ Notification creation
- ✅ Review system

---

## Production Deployment 🌐

1. **Set production environment variables** — Use a strong `SECRET_KEY`, set `FLASK_ENV=production`, `DEBUG=False`
2. **Switch to PostgreSQL** — Update `DATABASE_URL` connection string
3. **Apply migrations** — `flask db upgrade`
4. **Use a production WSGI server:**
   ```bash
   gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8000 app:app
   ```
5. **Enable HTTPS** with SSL/TLS certificates
6. **Setup monitoring** (Sentry, Datadog, etc.)

---

## Contributing 🤝

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Changelog 📜

### v1.1.0 (Current)
- ✅ Password reset via Gmail SMTP with styled HTML emails
- ✅ Flask-Migrate database migrations
- ✅ Timezone-aware matching with timezone bonus
- ✅ Skill proficiency levels (Beginner / Intermediate / Expert)
- ✅ Fuzzy skill name matching
- ✅ Improved error handling & user feedback

### v1.0.0
- ✅ Core platform with auth, skills, swaps, chat
- ✅ Gamification (XP, badges, levels)
- ✅ Security hardening (CSRF, rate limiting, secure sessions)
- ✅ Unit tests & logging

---

## License 📄

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Support 💬

For issues, suggestions, or questions:
- 📧 Email: luckyyyroyyy@gmail.com
- 🐛 [Open an Issue](https://github.com/luckyyyroyyy/Skill-Swap/issues)

---

<p align="center">
  <strong>Made with ❤️ for skill-sharing</strong><br/>
  <sub>© 2026 SkillSwap Pro — Swap skills, grow together.</sub>
</p>
