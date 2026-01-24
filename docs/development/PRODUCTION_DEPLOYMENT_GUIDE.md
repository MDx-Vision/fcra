# Production Deployment Guide

> Step-by-step guide to deploying Brightpath Ascend FCRA Platform to production
>
> **Created**: 2026-01-18

---

## Prerequisites

- [ ] Domain name (e.g., `app.brightpathascendgroup.com`)
- [ ] SSL certificate (Let's Encrypt or similar)
- [ ] PostgreSQL database (production)
- [ ] Server/hosting (Railway, Render, DigitalOcean, AWS, etc.)

---

## Step 1: Environment Variables

Create a `.env` file with production values:

```bash
# ===========================================
# DATABASE
# ===========================================
DATABASE_URL=postgresql://user:password@host:5432/fcra_production?sslmode=require

# ===========================================
# SECURITY
# ===========================================
SECRET_KEY=generate-a-strong-64-char-random-string
FLASK_ENV=production
CI=false

# ===========================================
# PAYMENT PROCESSING (Stripe)
# ===========================================
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxx

# ===========================================
# EMAIL (Gmail SMTP)
# ===========================================
GMAIL_USER=notifications@brightpathascendgroup.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
EMAIL_FROM_NAME=Brightpath Ascend Group

# ===========================================
# SMS (Twilio)
# ===========================================
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
TWILIO_MESSAGING_SERVICE_SID=MGxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ===========================================
# AI (Anthropic Claude)
# ===========================================
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx

# ===========================================
# PUSH NOTIFICATIONS (VAPID)
# ===========================================
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_CLAIMS_EMAIL=admin@brightpathascendgroup.com

# ===========================================
# CERTIFIED MAIL (SendCertified)
# ===========================================
SENDCERTIFIED_SFTP_HOST=sftp.sendcertifiedmail.com
SENDCERTIFIED_SFTP_PORT=22
SENDCERTIFIED_SFTP_USERNAME=your-username
SENDCERTIFIED_SFTP_PASSWORD=your-password

# ===========================================
# SCHEDULED JOBS (Cron Security)
# ===========================================
CRON_SECRET=generate-a-random-string-for-cron-auth

# ===========================================
# OPTIONAL: Sentry Error Tracking
# ===========================================
SENTRY_DSN=https://xxx@sentry.io/xxx
```

---

## Step 2: Database Setup

### 2.1 Create Production Database

```bash
# PostgreSQL
createdb fcra_production

# Or via psql
psql -c "CREATE DATABASE fcra_production;"
```

### 2.2 Run Migrations

The app auto-creates tables on first run. Alternatively:

```bash
# Set production DATABASE_URL
export DATABASE_URL="postgresql://..."

# Run the app once to create tables
python app.py
```

### 2.3 Create Admin User

```bash
# Via Python shell
python -c "
from database import get_db, Staff
from werkzeug.security import generate_password_hash

db = next(get_db())
admin = Staff(
    email='admin@brightpathascendgroup.com',
    password_hash=generate_password_hash('CHANGE_THIS_PASSWORD'),
    name='Admin User',
    role='admin',
    is_active=True
)
db.add(admin)
db.commit()
print('Admin created!')
"
```

---

## Step 3: Server Deployment

### Option A: Railway (Recommended - Easy)

1. Connect GitHub repo to Railway
2. Add environment variables in Railway dashboard
3. Railway auto-detects Flask and deploys

```bash
# Procfile (create if not exists)
web: gunicorn app:app --workers 4 --bind 0.0.0.0:$PORT
```

### Option B: Render

1. Create new Web Service
2. Connect to GitHub repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add environment variables

### Option C: DigitalOcean App Platform

1. Create App from GitHub
2. Select Python buildpack
3. Set run command: `gunicorn app:app --workers 4`
4. Add environment variables

### Option D: Traditional VPS (Ubuntu)

```bash
# Install dependencies
sudo apt update
sudo apt install python3.11 python3.11-venv postgresql nginx certbot

# Clone repo
git clone https://github.com/mdxvision/fcra.git /var/www/fcra
cd /var/www/fcra

# Setup venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Create systemd service
sudo nano /etc/systemd/system/fcra.service
```

```ini
# /etc/systemd/system/fcra.service
[Unit]
Description=FCRA Flask Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/fcra
Environment="PATH=/var/www/fcra/venv/bin"
EnvironmentFile=/var/www/fcra/.env
ExecStart=/var/www/fcra/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable fcra
sudo systemctl start fcra
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/fcra
server {
    listen 80;
    server_name app.brightpathascendgroup.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.brightpathascendgroup.com;

    ssl_certificate /etc/letsencrypt/live/app.brightpathascendgroup.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.brightpathascendgroup.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/fcra/static;
        expires 30d;
    }

    client_max_body_size 50M;
}
```

```bash
# Enable site and get SSL
sudo ln -s /etc/nginx/sites-available/fcra /etc/nginx/sites-enabled/
sudo certbot --nginx -d app.brightpathascendgroup.com
sudo systemctl reload nginx
```

---

## Step 4: Stripe Webhook Setup

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://app.brightpathascendgroup.com/api/webhooks/stripe`
3. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `charge.refunded`
   - `checkout.session.completed`
   - `customer.subscription.*` (all subscription events)
4. Copy webhook signing secret to `STRIPE_WEBHOOK_SECRET`

---

## Step 5: Scheduled Jobs (Cron)

Set up cron jobs to call the API endpoints:

```bash
# Edit crontab
crontab -e

# Add these lines:
# Hourly: Capture due payments, activate clients
0 * * * * curl -X POST "https://app.brightpathascendgroup.com/api/cron/hourly?secret=YOUR_CRON_SECRET"

# Daily at 6 AM: Expire stale holds, send reminders
0 6 * * * curl -X POST "https://app.brightpathascendgroup.com/api/cron/daily?secret=YOUR_CRON_SECRET"
```

---

## Step 6: Verification Checklist

After deployment, verify each component:

### Core Functionality
- [ ] Homepage loads (`/`)
- [ ] Staff login works (`/staff/login`)
- [ ] Dashboard loads after login
- [ ] Client portal login works (`/portal/login`)
- [ ] Signup form works (`/get-started`)

### Payment Processing
- [ ] Stripe checkout creates session
- [ ] Test payment succeeds (use test cards first!)
- [ ] Webhook receives events

### Communications
- [ ] Test email sends successfully
- [ ] Test SMS sends (check Twilio logs)
- [ ] Push notification subscription works

### Database
- [ ] Client creation works
- [ ] Data persists after restart

### Security
- [ ] HTTPS enforced (HTTP redirects)
- [ ] Rate limiting active
- [ ] Session cookies secure

---

## Step 7: Go Live Checklist

Before announcing to clients:

1. **Switch Stripe to Live Mode**
   - Replace `sk_test_` with `sk_live_` keys
   - Update webhook endpoint to use live signing secret
   - Test one real transaction

2. **Verify Email Deliverability**
   - Send test emails to various providers (Gmail, Outlook, Yahoo)
   - Check spam folders
   - Consider setting up SPF/DKIM/DMARC

3. **Load Testing** (Optional but recommended)
   ```bash
   # Simple load test
   ab -n 100 -c 10 https://app.brightpathascendgroup.com/
   ```

4. **Backup Strategy**
   - Set up automated database backups
   - Test restore process

5. **Monitoring**
   - Set up uptime monitoring (UptimeRobot, Pingdom)
   - Configure Sentry for error alerts
   - Set up log aggregation if needed

---

## Troubleshooting

### App won't start
```bash
# Check logs
journalctl -u fcra -f

# Check environment variables
printenv | grep -E "(DATABASE|STRIPE|GMAIL)"
```

### Database connection fails
```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1;"

# Check SSL mode
# Use sslmode=require for hosted databases
```

### Emails not sending
```bash
# Test Gmail connection
python -c "
import smtplib
s = smtplib.SMTP('smtp.gmail.com', 587)
s.starttls()
s.login('your@gmail.com', 'app-password')
print('Gmail connection OK!')
"
```

### Static files 404
```bash
# Check permissions
ls -la /var/www/fcra/static/

# Ensure nginx config has correct alias
```

---

## Support Contacts

| Service | Support |
|---------|---------|
| Stripe | https://support.stripe.com |
| Twilio | https://support.twilio.com |
| SendCertified | claudia@sendcertifiedmail.com |
| Anthropic (AI) | https://support.anthropic.com |

---

## Quick Commands Reference

```bash
# Restart app
sudo systemctl restart fcra

# View logs
journalctl -u fcra -f

# Check status
sudo systemctl status fcra

# Database backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Database restore
psql $DATABASE_URL < backup_20260118.sql
```

---

*Last Updated: 2026-01-18*
