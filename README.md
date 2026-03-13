# Skills-Swap 🤝

A modern skill-sharing platform where users can exchange knowledge and learn from each other through a gamified experience.

## Features ✨

- **User Authentication**: Secure registration and login system
- **Skill Marketplace**: Browse and discover complementary skills
- **Smart Matching Algorithm**: AI-powered user matching based on skills and reputation
- **Swap Requests**: Send and manage skill exchange requests
- **Real-time Chat**: Direct messaging for swap coordination (WebSocket)
- **Review System**: Rate and review completed swaps
- **Gamification**: 
  - XP points system
  - Achievement badges
  - User levels (Beginner → Skilled → Expert → Master)
  - Rating/reputation tracking
- **Notifications**: Real-time alerts for new requests and messages
- **User Profiles**: Customizable profiles with bio and profile picture

## Tech Stack 🛠️

- **Backend**: Flask, Flask-Login, Flask-SQLAlchemy, Flask-SocketIO
- **Database**: SQLite (development), PostgreSQL (production-ready)
- **Frontend**: HTML, CSS, JavaScript (Jinja2 templates)
- **Authentication**: Werkzeug Password Hashing
- **Form Validation**: Flask-WTF with WTForms
- **Real-time Communication**: Socket.IO (WebSocket)

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
├── app.py                 # Main Flask application
├── config.py              # Configuration management
├── extensions.py          # Flask extensions (DB, Login Manager, CSRF)
├── models.py              # Database models
├── routes.py              # Application routes
├── forms.py               # Form validation
├── utils.py               # Utility functions (matching, XP, badges)
├── test_app.py            # Unit tests
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (local)
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore file
│
├── static/               # Static files
│   ├── css/              # Stylesheets
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

- File upload validation needs hardening for production
- Real-time chat uses eventlet (not ideal for large scale)
- No rate limiting implemented
- No email verification system

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
- Contact: support@skillswap.com

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
