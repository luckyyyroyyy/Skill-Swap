# Deployment Guide 🚀

## Pre-Deployment Checklist ✅

- [ ] Change `SECRET_KEY` in `.env`
- [ ] Set `FLASK_ENV=production`
- [ ] Set `DEBUG=False`
- [ ] Use PostgreSQL database
- [ ] Enable HTTPS/SSL
- [ ] Setup proper logging
- [ ] Configure email service (if needed)
- [ ] Run full test suite
- [ ] Create database backups
- [ ] Setup monitoring and alerting

## Database Setup 🗄️

### PostgreSQL Installation

**Ubuntu/Debian:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres psql
postgres=# CREATE DATABASE skillswap;
postgres=# CREATE USER skillswap_user WITH PASSWORD 'strong-password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE skillswap TO skillswap_user;
postgres=# \q
```

**macOS (Homebrew):**
```bash
brew install postgresql
brew services start postgresql
psql -U postgres
postgres=# CREATE DATABASE skillswap;
postgres=# CREATE USER skillswap_user WITH PASSWORD 'strong-password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE skillswap TO skillswap_user;
```

### Update `.env`
```
DATABASE_URL=postgresql://skillswap_user:strong-password@localhost/skillswap
```

### Initialize Database
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## Server Setup 🖥️

### Option 1: Gunicorn + Nginx (Recommended)

1. **Install Gunicorn:**
   ```bash
   pip install gunicorn
   ```

2. **Create systemd service** (`/etc/systemd/system/skillswap.service`):
   ```ini
   [Unit]
   Description=Skills-Swap Application
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/var/www/skillswap
   ExecStart=/var/www/skillswap/venv/bin/gunicorn \
     --worker-class eventlet \
     -w 1 \
     --bind unix:/var/www/skillswap/skillswap.sock \
     --timeout 60 \
     --access-logfile /var/log/skillswap/access.log \
     --error-logfile /var/log/skillswap/error.log \
     app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

3. **Create nginx config** (`/etc/nginx/sites-available/skillswap`):
   ```nginx
   upstream skillswap {
       server unix:/var/www/skillswap/skillswap.sock fail_timeout=0;
   }

   server {
       listen 80;
       server_name skillswap.com www.skillswap.com;
       return 301 https://$server_name$request_uri;
   }

   server {
       listen 443 ssl http2;
       server_name skillswap.com www.skillswap.com;
       
       ssl_certificate /etc/ssl/certs/skillswap.crt;
       ssl_certificate_key /etc/ssl/private/skillswap.key;
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers HIGH:!aNULL:!MD5;

       client_max_body_size 16M;

       location / {
           proxy_pass http://skillswap;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           
           # WebSocket support
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }

       location /static/ {
           alias /var/www/skillswap/static/;
           expires 30d;
       }
   }
   ```

4. **Enable and start services:**
   ```bash
   sudo systemctl enable skillswap
   sudo systemctl start skillswap
   sudo systemctl enable nginx
   sudo systemctl restart nginx
   ```

### Option 2: Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 8000

CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:8000", "app:app"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: skillswap
      POSTGRES_USER: skillswap_user
      POSTGRES_PASSWORD: strong-password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://skillswap_user:strong-password@db:5432/skillswap
      FLASK_ENV: production
      SECRET_KEY: your-secret-key
    depends_on:
      - db
    volumes:
      - ./static:/app/static

volumes:
  postgres_data:
```

Deploy with Docker:
```bash
docker-compose up -d
```

## SSL/TLS Configuration 🔒

### Using Let's Encrypt (Free)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d skillswap.com -d www.skillswap.com
```

Configure auto-renewal:
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

## Environment Variables (Production) 🔐

Create `.env` with production values:
```
SECRET_KEY=generate-a-secure-random-key
FLASK_ENV=production
DATABASE_URL=postgresql://user:password@host:5432/skillswap
UPLOAD_FOLDER=/var/www/skillswap/uploads
DEBUG=False

# Optional: Email configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

## Monitoring & Logging 📊

### Application Logs
```bash
# Monitor real-time logs
tail -f /var/log/skillswap/error.log
tail -f /var/log/skillswap/access.log
```

### Database Maintenance
```sql
-- Backup database
pg_dump -U skillswap_user skillswap > backup.sql

-- Restore from backup
psql -U skillswap_user skillswap < backup.sql
```

### Health Check Script (`/var/www/skillswap/health_check.sh`)
```bash
#!/bin/bash
curl -f http://localhost:8000/ || exit 1
```

Schedule with cron:
```bash
*/5 * * * * /var/www/skillswap/health_check.sh || systemctl restart skillswap
```

## Performance Optimization ⚡

### Database Query Optimization
```python
# Use lazy loading for relationships
skills = user.skills.lazy(False)  # Eager load
```

### Caching
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/dashboard')
@cache.cached(timeout=300)
def dashboard():
    # Cached for 5 minutes
    pass
```

### CDN for Static Files
```python
# Configure Flask to use CDN
app.config['CDN_DOMAIN'] = 'https://cdn.example.com'
```

## Security Hardening 🛡️

### Rate Limiting
```bash
pip install Flask-Limiter
```

```python
from flask_limiter import Limiter

limiter = Limiter(app)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    pass
```

### CORS Configuration (if needed)
```python
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "trusted-domain.com"}})
```

## Backup Strategy 💾

### Automated Daily Backups
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backups/skillswap"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

pg_dump -U skillswap_user skillswap | gzip > $BACKUP_DIR/skillswap_$TIMESTAMP.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "skillswap_*.sql.gz" -mtime +30 -delete
```

Schedule with cron:
```bash
0 2 * * * /path/to/backup.sh  # Daily at 2 AM
```

## Troubleshooting 🔧

### Application won't start
```bash
# Check logs
journalctl -u skillswap.service -n 50
# Check database connection
psql -U skillswap_user -d skillswap -c "SELECT 1"
```

### WebSocket connection issues
- Ensure proxy properly handles WebSocket upgrades
- Check firewall rules for port 8000
- Verify eventlet workers are running

### High memory usage
```bash
# Restart application to free memory
sudo systemctl restart skillswap
```

## Scaling Considerations 📈

For larger deployments:
1. Use Redis for session storage
2. Implement database read replicas
3. Use multiple Gunicorn workers
4. Add load balancer (HAProxy/nginx)
5. Consider message queue for async tasks (Celery)

## Support & Resources 📚

- Flask Deployment: https://flask.palletsprojects.com/deployment/
- Gunicorn: https://gunicorn.org/
- Nginx: https://nginx.org/
- PostgreSQL: https://postgresql.org/
- Let's Encrypt: https://letsencrypt.org/

---

**Last Updated:** 2024
**Version:** 1.0.0
