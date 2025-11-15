# Quick Start Guide - AI Polling System

Get your polling system up and running in 5 minutes!

## 🚀 Quick Setup (Windows)

### Step 1: Install Python
Download Python 3.8+ from [python.org](https://www.python.org/downloads/)

### Step 2: Setup Project

Open Command Prompt or PowerShell and run:

```cmd
# Create project folder
mkdir polling_system
cd polling_system

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install Flask Flask-SQLAlchemy Flask-Login Werkzeug matplotlib reportlab Pillow python-dateutil
```

### Step 3: Create File Structure

Create these folders:
```cmd
mkdir static\uploads\profiles
mkdir static\uploads\polls
mkdir templates
```

### Step 4: Add Files

Copy all the provided files into their respective locations:
- `app.py` → Root folder
- `config.py` → Root folder  
- `init_db.py` → Root folder
- `requirements.txt` → Root folder
- All HTML files → `templates` folder

### Step 5: Initialize Database

```cmd
python init_db.py --with-samples
```

This creates:
- ✅ Database with all tables
- ✅ Admin account (admin@polls.com / Admin@123)
- ✅ 5 sample users (password: Test@123)
- ✅ 8 sample polls with votes and comments

### Step 6: Run Application

```cmd
python app.py
```

Open browser and visit: **http://localhost:5000**

---

## 🚀 Quick Setup (Linux/Mac)

### Step 1: Install Python
Python usually comes pre-installed. Check version:
```bash
python3 --version
```

### Step 2: Setup Project

```bash
# Create project folder
mkdir polling_system
cd polling_system

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install Flask Flask-SQLAlchemy Flask-Login Werkzeug matplotlib reportlab Pillow python-dateutil
```

### Step 3: Create File Structure

```bash
mkdir -p static/uploads/profiles
mkdir -p static/uploads/polls
mkdir templates
```

### Step 4: Add Files

Copy all the provided files into their respective locations:
- `app.py` → Root folder
- `config.py` → Root folder
- `init_db.py` → Root folder
- `requirements.txt` → Root folder
- All HTML files → `templates` folder

### Step 5: Initialize Database

```bash
python3 init_db.py --with-samples
```

### Step 6: Run Application

```bash
python3 app.py
```

Open browser and visit: **http://localhost:5000**

---

## 📁 Complete File Structure

```
polling_system/
│
├── app.py                          # Main Flask application
├── config.py                       # Configuration settings
├── init_db.py                      # Database initialization
├── requirements.txt                # Python dependencies
├── README.md                       # Full documentation
├── QUICKSTART.md                   # This file
│
├── static/
│   └── uploads/
│       ├── profiles/               # User profile pictures
│       └── polls/                  # Poll images
│
└── templates/
    ├── base.html                   # Base template
    ├── index.html                  # Homepage
    ├── register.html               # Registration page
    ├── login.html                  # Login page
    ├── create_poll.html            # Create poll form
    ├── view_poll.html              # Poll details & voting
    ├── profile.html                # User profile
    ├── leaderboard.html            # Leaderboard page
    └── admin_dashboard.html        # Admin panel
```

---

## 🔑 Default Accounts

### Admin Account
```
Email: admin@polls.com
Password: Admin@123
```

### Sample User Accounts (if using --with-samples)
```
john@example.com    → Password: Test@123
jane@example.com    → Password: Test@123
bob@example.com     → Password: Test@123
alice@example.com   → Password: Test@123
charlie@example.com → Password: Test@123
```

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Homepage loads at http://localhost:5000
- [ ] Can register a new account
- [ ] Can login with admin credentials
- [ ] Can create a new poll
- [ ] Can vote on polls
- [ ] Can add comments
- [ ] Can add reactions
- [ ] Can view leaderboard
- [ ] Admin can access dashboard at /admin
- [ ] Can export poll results as PDF

---

## 🐛 Common Issues & Solutions

### Issue: "Module not found" error
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "Permission denied" on uploads folder
**Solution (Linux/Mac):**
```bash
chmod -R 755 static/uploads
```

**Solution (Windows):**
Right-click folder → Properties → Security → Edit → Allow full control

### Issue: "Port 5000 already in use"
**Solution:**
Change port in `app.py` (last line):
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Issue: Database errors
**Solution:**
Delete and recreate database:
```bash
# Delete old database
rm polling_system.db

# Recreate database
python init_db.py --with-samples
```

---

## 📊 What's Included

### Features Available After Setup:
1. ✅ **User Management**
   - Registration with validation
   - Login/Logout
   - Profile management
   - Profile pictures

2. ✅ **Poll System**
   - Create polls with images
   - Multiple choice options
   - Scheduled polls
   - Poll expiration
   - Masked polls

3. ✅ **Voting**
   - Registered user voting
   - Guest voting (with email)
   - One vote per user/email
   - Real-time results

4. ✅ **Engagement**
   - Comments with replies
   - Reactions (5 types)
   - Sentiment analysis
   - Social sharing

5. ✅ **Gamification**
   - Badges system
   - Leaderboards
   - User statistics

6. ✅ **Admin Panel**
   - User management
   - Poll moderation
   - Comment moderation
   - Analytics dashboard

7. ✅ **Extras**
   - PDF export
   - Search & filters
   - Categories
   - Responsive design

---

## 🎯 Next Steps

After successfully running the application:

1. **Customize Branding**
   - Update colors in `base.html`
   - Add your logo
   - Change site name

2. **Security**
   - Change admin password
   - Update SECRET_KEY in `config.py`
   - Enable HTTPS in production

3. **Add Features**
   - Email notifications
   - 2FA authentication
   - Advanced analytics
   - API endpoints

4. **Deploy**
   - Use Gunicorn (Linux)
   - Use Waitress (Windows)
   - Deploy on Heroku/AWS/DigitalOcean

---

## 📚 Additional Resources

- Full Documentation: See `README.md`
- Flask Documentation: https://flask.palletsprojects.com/
- SQLAlchemy Docs: https://docs.sqlalchemy.org/
- Bootstrap 5 Docs: https://getbootstrap.com/docs/5.3/

---

## 💡 Tips

1. **Use the sample data** when learning the system
2. **Start with admin account** to see all features
3. **Test all features** before deploying
4. **Backup database** before making changes
5. **Read error messages** - they're usually helpful!

---

## 🎉 You're All Set!

Your AI-Powered Polling System is ready to use. Start by:
1. Creating your first poll
2. Inviting users to vote
3. Exploring the leaderboard
4. Checking out the admin dashboard

**Happy Polling! 🗳️**