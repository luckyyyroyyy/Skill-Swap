# Skills-Swap 🤝

A modern skill-sharing platform where users can exchange knowledge and learn from each other through a gamified experience.

## Database Models 🗄️

The application uses the following data models:

- **User**: Stores user account info, bio, profile picture, XP, badges, rating, and level
- **Skill**: User-offered and user-wanted skills  
- **SwapRequest**: Tracks skill exchange requests with status (pending/accepted/rejected/completed)
- **Review**: User ratings and comments for completed swaps
- **UserBadge**: Achievement badges earned through gamification

## Features ✨

- **User Authentication**: Secure registration and login with password hashing
- **Skill Marketplace**: Browse and discover users offering/wanting specific skills
- **Smart Matching**: Connect users based on complementary skills
- **Swap Requests**: Send and manage skill exchange requests with status tracking
- **Real-time Chat**: Direct messaging with WebSocket support for instant communication
- **Review System**: Rate and review users after completed swaps
- **Gamification**: 
  - XP points system for completing swaps
  - Achievement badges
  - User levels: Beginner → Skilled → Expert → Master
  - Rating and reputation tracking
- **Notifications**: Stay updated on swap requests and messages
- **User Profiles**: Customizable profiles with bio and profile picture uploads
- **Security Features**: CSRF protection, rate limiting, secure session handling

## Tech Stack 🛠️

- **Backend Framework**: Flask 3.1.2, Flask-Login, Flask-SQLAlchemy
- **Real-time Communication**: Flask-SocketIO, python-socketio, python-engineio
- **Database**: SQLite (development), PostgreSQL (production-ready)
- **Frontend**: HTML, CSS, JavaScript with Jinja2 templates
- **Authentication**: Flask-Login with Werkzeug password hashing
- **Form Validation**: Flask-WTF, WTForms, email-validator
- **Security**: CSRF Protection enabled, Rate limiting, Secure session handling
- **Event Handler**: eventlet
- **Environment Management**: python-dotenv

## Setup & Installation 🚀

### Prerequisites
- Python 3.9+
- pip (Python package manager)
- Virtual environment (recommended)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Skills-Swap
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your configuration:
   ```
   SECRET_KEY=your-secret-key-here
   FLASK_ENV=development
   DATABASE_URL=sqlite:///skillswap.db
   ```

5. **Initialize the database**
   ```bash
   python
   >>> from app import app, db
   >>> with app.app_context():
   ...     db.create_all()
   >>> exit()
   ```

6. **Run the application**
   ```bash
   python -m flask run
   ```
   The app will be available at `http://localhost:5000`

## Project Structure 📁

```
Skills-Swap/
├── app.py                 # Main Flask application with SocketIO
├── config.py              # Configuration management (Dev/Prod/Test)
├── extensions.py          # Flask extensions (DB, Login Manager, CSRF, Limiter)
├── models.py              # Database models (User, Skill, SwapRequest, Review)
├── forms.py               # Form validation with Flask-WTF
├── utils.py               # Utility functions
├── test_app.py            # Unit tests
├── requirements.txt       # Python dependencies
├── DEPLOYMENT.md          # Deployment guide
├── .env                   # Environment variables (local)
├── .env.example          # Environment variables template
│
├── routes/                # Application blueprints
│   ├── main.py            # Landing page
│   ├── auth.py            # Authentication (register, login, logout)
│   ├── user.py            # User profile management
│   ├── swap.py            # Skill swap requests and matching
│   ├── chat.py            # Real-time messaging
│   └── __init__.py
│
├── static/               # Static files
│   ├── css/              # Stylesheets (style.css, animations.css)
│   │   ├── style.css
│   │   └── animations.css
│   ├── js/               # JavaScript files
│   │   ├── main.js
│   │   └── animations.js
│   └── profile_pics/     # User profile pictures
│
├── templates/            # Jinja2 templates
│   ├── base.html
│   ├── landing.html
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│   ├── profile.html
│   ├── edit_profile.html
│   ├── my_swaps.html
│   ├── chat.html
│   ├── notifications.html
│   └── matches.html
│
└── instance/             # Instance-specific files
    └── skillswap.db      # SQLite database
```

## API Routes 📡

### Authentication
- `GET /` - Landing page
- `GET/POST /register` - User registration
- `GET/POST /login` - User login
- `GET /logout` - User logout

### Dashboard & Matching
- `GET /dashboard` - View matched users
- `GET/POST /profile/<username>` - View user profile
- `GET/POST /edit_profile` - Edit profile
- `POST /add_skill` - Add a new skill

### Swaps
- `POST /send_swap/<user_id>` - Send swap request
- `GET/POST /my-swaps` - View all swaps
- `GET /accept/<swap_id>` - Accept swap request
- `GET /reject/<swap_id>` - Reject swap request
- `GET /complete/<swap_id>` - Complete swap
- `POST /submit_review/<user_id>` - Submit review

### Chat & Notifications
- `GET/POST /chat/<swap_id>` - Chat for swap
- `GET /notifications` - View notifications

## Key Features Explained 🎯

### Matching Algorithm
The smart matching algorithm calculates compatibility scores based on:
- **Mutual Skills** (40%): Skills user A wants that B offers + vice versa
- **Reputation** (40%): User B's average rating and reviews
- **Experience** (20%): User B's XP level

### XP System
Users earn XP through:
- Adding skills: +10 XP
- Completing swaps: +50 XP per user
- Receiving reviews: +50 XP per user

### Badge System
Unlock achievements by:
- **First Swap**: Complete 1 swap
- **Rising Star**: Earn 200 XP
- **Skill Master**: Earn 500 XP
- **Trusted Mentor**: Receive 5 positive reviews

## Security Features 🔒

- **CSRF Protection**: Flask-WTF CSRF tokens on all forms
- **Password Hashing**: Werkzeug secure password hashing
- **Session Security**: Secure session cookies with HTTPOnly flag
- **Input Validation**: WTForms validation on all inputs
- **Authorization Checks**: Role-based access control on all routes
- **SQL Injection Prevention**: SQLAlchemy ORM parameterized queries

## Testing 🧪

Run the test suite:
```bash
pip install pytest
pytest test_app.py -v
```

Tests cover:
- User model operations
- Skill management
- Swap request creation
- Matching algorithm
- Badge system
- Notifications

## Logging 📝

Application logs are written to `skillswap.log` and console:
- Authentication events
- Swap operations
- Badge awards
- Errors and exceptions

## Environment Variables 🔐

| Variable | Default | Description |
|----------|---------|-------------|
| SECRET_KEY | dev-key | Flask secret key (change in production!) |
| FLASK_ENV | development | Application environment |
| DATABASE_URL | sqlite:///skillswap.db | Database connection string |
| UPLOAD_FOLDER | static/profile_pics | Profile picture upload location |
| DEBUG | True | Enable debug mode (set to False in production) |

## Production Deployment 🌐

1. **Update `.env`** with production values
2. **Use PostgreSQL** instead of SQLite
3. **Set `DEBUG=False`** and `SESSION_COOKIE_SECURE=True`
4. **Use a production WSGI server** (Gunicorn, uWSGI)
5. **Enable HTTPS** with SSL certificates
6. **Setup error monitoring** (Sentry, etc.)

Example production run:
```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8000 app:app
```

## Known Limitations ⚠️

- Real-time chat uses eventlet (not ideal for large scale deployments)
- No email verification system implemented
- Profile picture upload limited to 2MB files
- WebSocket connections limited by single-threaded eventlet worker

## Future Enhancements 🔮

- [ ] Two-factor authentication
- [ ] Email notifications
- [ ] Video/call integration
- [ ] Skill categories and subcategories
- [ ] Advanced search and filtering
- [ ] User blocking system
- [ ] Dispute resolution system
- [ ] Payment integration for premium features
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard

## Contributing 🤝

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see LICENSE file for details.

## Support 💬

For issues, suggestions, or questions:
- Open an issue on GitHub
- Contact: luckyyyroyyy@gmail.com

## Changelog 📜

### Version 1.0.0 (Current)
- ✅ Initial release with core features
- ✅ Security hardening complete
- ✅ Unit tests implemented
- ✅ Full documentation
- ✅ Environment configuration
- ✅ Form validation
- ✅ Error handling and logging

---

**Made with ❤️ for skill-sharing**
